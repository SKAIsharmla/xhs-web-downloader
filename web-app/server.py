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
    return {
        "work_path": cfg["download_dir"],
        "image_format": cfg["image_format"],
        "folder_mode": cfg["folder_mode"],
        "author_archive": cfg["author_archive"],
        "cookie": cfg.get("cookie", ""),
        "download_record": True,
        "language": "zh_CN",
    }


web_config = WebConfig()

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
        result = await xhs.extract(req.url, download=True, index=req.index)
        if not result:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "下载失败，无法获取作品数据",
                },
            )

        data = result[0] if result[0] else {}
        total = len(req.index) if req.index else len(data.get("下载地址", []))

        return {
            "success": True,
            "message": "下载任务已完成",
            "data": {
                "作品标题": data.get("作品标题", ""),
                "作者昵称": data.get("作者昵称", ""),
                "下载数量": total,
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
