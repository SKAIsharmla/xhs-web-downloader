# Copyright (C) 2025 SKAIsharmla
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import re
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add XHS-Downloader to Python path
XHS_DOWNLOADER_PATH = Path(__file__).resolve().parent.parent / "XHS-Downloader"
sys.path.insert(0, str(XHS_DOWNLOADER_PATH))

from config import WebConfig
from source import XHS

# ---------------------------------------------------------------------------
# Configuration mapping
# ---------------------------------------------------------------------------

def _map_config_to_xhs(cfg: dict) -> dict:
    # XHS-Downloader 内部会创建 {work_path}/{folder_name}/ 作为下载目录。
    # 将用户配置的 download_dir 拆分为父路径和文件夹名，避免多出一层 "Download/"。
    dl = Path(cfg["download_dir"])
    return {
        "work_path": str(dl.parent),
        "folder_name": dl.name,
        "image_format": cfg["image_format"],
        "folder_mode": cfg["folder_mode"],
        "author_archive": cfg["author_archive"],
        "cookie": cfg.get("cookie", ""),
        "download_record": True,
        "language": "zh_CN",
    }


web_config = WebConfig()

# 解析结果缓存：避免下载时重新请求小红书页面（可能被限流）
_note_cache: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class ParseRequest(BaseModel):
    url: str
    cookie: Optional[str] = None


class DownloadRequest(BaseModel):
    url: str
    index: Optional[list[int]] = None
    cookie: Optional[str] = None


class SettingsUpdate(BaseModel):
    download_dir: Optional[str] = None
    image_format: Optional[str] = None
    folder_mode: Optional[bool] = None
    author_archive: Optional[bool] = None
    cookie: Optional[str] = None
    server_host: Optional[str] = None
    server_port: Optional[int] = None

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = web_config.load()

    # Init XHS core
    xhs = XHS(**_map_config_to_xhs(cfg))
    await xhs.__aenter__()
    app.state.xhs = xhs

    # Dedicated HTTP client for image proxying (the XHS internal clients have
    # strict fingerprinting that can interfere with simple CDN fetches).
    app.state.image_client = httpx.AsyncClient(
        headers={
            "Referer": "https://www.xiaohongshu.com/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/143.0.0.0 Safari/537.36"
            ),
        },
        follow_redirects=True,
        timeout=30.0,
    )

    yield

    await app.state.xhs.__aexit__(None, None, None)
    await app.state.image_client.aclose()


app = FastAPI(
    title="小红书图片下载器",
    description="局域网小红书图片下载工具",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.post("/api/parse")
async def parse_link(req: ParseRequest):
    """解析小红书链接，返回帖子信息和图片列表（不下载）"""
    xhs: XHS = app.state.xhs
    try:
        result = await xhs.extract(req.url, download=False)
        if not result or not result[0]:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "解析失败，请检查链接是否有效",
                    "data": None,
                },
            )

        data = result[0]
        # 缓存解析结果，下载时直接用缓存的图片 URL，避免重新请求页面
        if pid := data.get("作品ID"):
            _note_cache[pid] = data

        img_urls = data.get("下载地址", [])
        live_urls = data.get("动图地址", []) or [None] * len(img_urls)

        images = [
            {
                "index": i,
                "url": url,
                "live_url": live_urls[i - 1] if i <= len(live_urls) else None,
            }
            for i, url in enumerate(img_urls, start=1)
        ]

        return {
            "success": True,
            "message": "解析成功",
            "data": {
                "作品ID": data.get("作品ID", ""),
                "作品标题": data.get("作品标题", ""),
                "作品描述": data.get("作品描述", ""),
                "作品类型": data.get("作品类型", ""),
                "作者昵称": data.get("作者昵称", ""),
                "作者ID": data.get("作者ID", ""),
                "发布时间": data.get("发布时间", ""),
                "点赞数量": data.get("点赞数量", "0"),
                "图片列表": images,
            },
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"解析失败：{str(e)}", "data": None},
        )


@app.post("/api/download")
async def download_images(req: DownloadRequest):
    """下载指定序号的图片到服务器"""
    xhs: XHS = app.state.xhs
    try:
        # 优先尝试解析（网络请求可能会被限流）
        result = await xhs.extract(req.url, download=False)
        if result and result[0] and result[0].get("下载地址"):
            data = result[0]
        else:
            # 解析失败，尝试从缓存中获取之前解析的数据
            cached = None
            for pid, d in _note_cache.items():
                if pid in req.url:
                    cached = d
                    break
            if not cached or not cached.get("下载地址"):
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": "获取作品数据失败，请先解析链接"},
                )
            data = cached

        # 手动调用下载引擎（不需要重新请求小红书页面）
        name = xhs._XHS__naming_rules(data)
        nickname = data["作者ID"] + "_" + xhs.CLEANER.filter_name(data["作者昵称"])
        _, dl_results = await xhs.download.run(
            data["下载地址"],
            data.get("动图地址", [None] * len(data["下载地址"])),
            req.index,
            nickname,
            name,
            data["作品类型"],
            data["时间戳"],
        )

        success = sum(1 for r in dl_results if r)
        if success:
            await xhs._XHS__add_record(data["作品ID"])
            await xhs.save_data(data)

        return {
            "success": True,
            "message": f"下载完成！共 {success} 张图片已保存到服务器",
            "data": {
                "作品标题": data.get("作品标题", ""),
                "作者昵称": data.get("作者昵称", ""),
                "下载数量": success,
            },
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"下载失败：{str(e)}"},
        )


@app.get("/api/settings")
async def get_settings():
    cfg = web_config.load()
    return {
        "success": True,
        "data": {
            "download_dir": cfg["download_dir"],
            "image_format": cfg["image_format"],
            "folder_mode": cfg["folder_mode"],
            "author_archive": cfg["author_archive"],
            "has_cookie": bool(cfg.get("cookie", "")),
        },
    }


@app.post("/api/settings")
async def update_settings(update: SettingsUpdate):
    cfg = web_config.save(update.model_dump(exclude_none=True))

    # Reinitialise the XHS singleton with the new config
    await app.state.xhs.__aexit__(None, None, None)
    object.__setattr__(XHS, "_XHS__INSTANCE", None)  # reset singleton

    xhs = XHS(**_map_config_to_xhs(cfg))
    await xhs.__aenter__()
    app.state.xhs = xhs

    return {"success": True, "message": "设置已保存"}


@app.get("/api/image")
async def proxy_image(url: str):
    """代理加载小红书图片（解决 CDN 跨域/防盗链问题）"""
    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="无效的图片 URL")

    client: httpx.AsyncClient = app.state.image_client
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "image/jpeg")
        return Response(
            content=resp.content,
            media_type=content_type,
            headers={"Cache-Control": "public, max-age=3600"},
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"图片加载失败：{str(e)}")

# ---------------------------------------------------------------------------
# Static files (frontend)
# ---------------------------------------------------------------------------

frontend_path = Path(__file__).resolve().parent / "frontend"
if frontend_path.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(frontend_path), html=True),
        name="frontend",
    )
