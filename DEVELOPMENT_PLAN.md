# 小红书图片下载 Web 应用 — 开发文档

## 一、项目概述

基于现有的 [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader) 项目，构建一个 **Web 版小红书图片下载工具**。

### 使用场景
1. 部署在局域网 Linux 服务器上，启动一个 Web 服务
2. 用户通过 Windows 浏览器访问网页
3. 在网页中粘贴小红书帖子链接
4. 网页自动解析帖子信息，展示所有图片供用户勾选
5. 点击下载按钮，图片保存到 Linux 服务器上配置好的目录

### 为什么要复用现有项目
现有 `XHS-Downloader` 已经解决了小红书最难的部分：
- 小红书链接解析（支持 `/explore/`、`/discovery/item/`、`xhslink.com` 短链）
- 网页数据抓取（反爬处理、Cookie 管理）
- 图片下载地址提取（支持多种格式：PNG/WEBP/JPEG/HEIC）
- 文件下载（断点续传、文件签名校验、重试机制）
- 视频/动图下载

我们只需要在其基础上添加一个 **Web 前端界面**，并简化配置即可。

---

## 二、项目结构

```
小红书下载/
├── XHS-Downloader/          # 现有项目（作为核心库使用）
│   └── source/              # 核心代码（不动它）
│       ├── application/     # 核心逻辑（app.py, download.py, image.py, explore.py, request.py）
│       ├── module/          # 配置管理（manager.py, settings.py, static.py）
│       └── expansion/       # 工具类（namespace.py, cleaner.py, converter.py）
│
└── web-app/                 # 新建的 Web 应用
    ├── main.py              # 启动入口
    ├── server.py            # FastAPI Web 服务器
    ├── config.py            # Web 应用配置
    ├── settings.json        # 配置文件（下载目录等）
    ├── frontend/
    │   ├── index.html       # 前端页面
    │   ├── style.css        # 样式
    │   └── app.js           # 前端逻辑
    ├── downloads/            # 默认下载目录（可在配置中修改）
    └── requirements.txt     # 额外依赖
```

---

## 三、技术选型

| 层 | 技术 | 理由 |
|---|------|------|
| **后端框架** | FastAPI + Uvicorn | 现有项目已有 FastAPI 依赖，异步支持好，自带 API 文档 |
| **前端** | 原生 HTML/CSS/JS | 无需 npm/build 步骤，部署简单，局域网场景不需要现代框架 |
| **HTTP 客户端** | httpx（已有） | 现有项目已使用，复用即可 |
| **CSS 框架** | 无 / 少量手写 | 保持轻量，或用 Pico.css 等极小 CSS 库 |
| **Python 版本** | >= 3.12 | 与现有项目一致 |

---

## 四、后端 API 设计

所有 API 前缀：`/api`

### 4.1 POST /api/parse — 解析链接

解析小红书帖子链接，返回帖子信息和图片列表（不下载）。

**请求体：**
```json
{
  "url": "https://www.xiaohongshu.com/explore/xxxxx",
  "cookie": ""  // 可选，登录态 Cookie
}
```

**响应体：**
```json
{
  "success": true,
  "data": {
    "作品ID": "xxxxx",
    "作品标题": "标题文本",
    "作品描述": "描述文本",
    "作品类型": "图文",       // "图文" | "视频" | "图集"
    "作者昵称": "某某",
    "作者ID": "xxx",
    "发布时间": "2025-01-01_12:00:00",
    "点赞数量": "100",
    "图片列表": [
      { "序号": 1, "下载地址": "https://ci.xiaohongshu.com/...", "动图地址": null },
      { "序号": 2, "下载地址": "https://ci.xiaohongshu.com/...", "动图地址": null }
    ],
    "动图地址": []            // 动图列表（如果有的话）
  },
  "message": "解析成功"
}
```

### 4.2 POST /api/download — 下载图片

根据用户勾选的图片序号，下载指定图片到服务器。

**请求体：**
```json
{
  "url": "https://www.xiaohongshu.com/explore/xxxxx",
  "index": [1, 3, 5],     // 要下载的图片序号，null 表示下载全部
  "cookie": ""             // 可选
}
```

**响应体（SSE 流式或普通 JSON）：**
```json
{
  "success": true,
  "message": "下载完成",
  "files": [
    { "name": "作者_标题_1.jpg", "path": "/downloads/xxx/", "success": true },
    { "name": "作者_标题_3.jpg", "path": "/downloads/xxx/", "success": true }
  ]
}
```

### 4.3 GET /api/settings — 获取配置

```json
{
  "download_dir": "/home/user/xhs-downloads",
  "image_format": "jpeg",
  "folder_mode": false,
  "author_archive": false
}
```

### 4.4 POST /api/settings — 更新配置

```json
{
  "download_dir": "/home/user/xhs-downloads",
  "image_format": "jpeg"
}
```

---

## 五、前端页面设计

### 5.1 布局结构

```
┌──────────────────────────────────────────────────────┐
│  🔴 小红书图片下载器                    [⚙ 设置]      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │  粘贴小红书链接...                    [解析]   │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ┌─ 解析结果 ──────────────────────────────────┐    │
│  │  标题：xxxx   作者：xxxx   时间：xxxx         │    │
│  │  类型：图文   图片数量：12                    │    │
│  │                                              │    │
│  │  [全选] [取消全选]                           │    │
│  │                                              │    │
│  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐        │    │
│  │  │ 1  │ │ 2  │ │ 3  │ │ 4  │ │ 5  │  ...   │    │
│  │  │ ☑  │ │ ☑  │ │ ☐  │ │ ☑  │ │ ☐  │        │    │
│  │  └────┘ └────┘ └────┘ └────┘ └────┘        │    │
│  │                                              │    │
│  │  [⬇ 下载选中图片 (3张)]                     │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ┌─ 下载状态 ──────────────────────────────────┐    │
│  │  ✅ 图片1.jpg - 下载成功                      │    │
│  │  ⏳ 图片3.jpg - 下载中... 45%                 │    │
│  │  ❌ 图片5.jpg - 下载失败：网络超时             │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 5.2 交互流程

1. 用户粘贴链接 → 点击"解析"按钮
2. 前端调用 `POST /api/parse`，显示加载动画
3. 解析成功后展示帖子信息和图片缩略图网格
4. 用户勾选/取消勾选要下载的图片（默认全选）
5. 点击"下载选中图片"按钮
6. 前端调用 `POST /api/download`，显示每张图片下载进度
7. 下载完成，显示成功/失败统计

### 5.3 设置弹窗

```
┌─ 设置 ────────────────────────────┐
│  下载目录：[/home/user/downloads]  │
│  图片格式：[JPEG ▾]               │
│  按作者归档：[  ]                  │
│  Cookie：  [_____________] （选填）│
│                                    │
│  [保存设置]                        │
└────────────────────────────────────┘
```

---

## 六、核心实现要点

### 6.1 复用现有代码的方式

现有项目的 `source/` 目录是一个完整的 Python 包，可以直接 import：

```python
import sys
sys.path.insert(0, "/path/to/XHS-Downloader")

from source import XHS  # 主类，包含 extract() 方法
from source import Settings
```

`XHS` 类的关键方法：
- `extract(url, download=False, index=None)` — 提取帖子数据，可选下载
  - `url`: 小红书链接
  - `download`: 是否同时下载文件
  - `index`: 指定下载图片序号列表（如 `[1, 3, 5]`），`None` 表示全部下载
  - 返回：`list[dict]`，每个 dict 包含完整的帖子信息

### 6.2 后端实现思路（server.py）

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from source import XHS, Settings

app = FastAPI()

# 初始化 XHS 实例（使用 settings.json 配置）
settings = Settings().run()
xhs = None  # 在 lifespan 中创建

@app.on_event("startup")
async def startup():
    global xhs
    xhs = await XHS(**settings).__aenter__()

@app.on_event("shutdown")
async def shutdown():
    await xhs.__aexit__(None, None, None)

@app.post("/api/parse")
async def parse_link(request: ParseRequest):
    """解析链接，返回帖子信息和图片列表（不下载）"""
    data = await xhs.extract(request.url, download=False)
    # 提取图片列表供前端展示
    return format_response(data)

@app.post("/api/download")
async def download_images(request: DownloadRequest):
    """下载指定序号的图片"""
    data = await xhs.extract(
        request.url,
        download=True,
        index=request.index,  # [1, 3, 5] 或 None（全部）
    )
    return format_download_result(data)

# 挂载静态文件目录（前端页面）
app.mount("/", StaticFiles(directory="frontend", html=True))
```

### 6.3 图片预览的实现

小红书图片 URL 需要带上 Referer 请求头才能访问。有两种方案：

**方案 A：服务端代理（推荐）**
- 添加一个 API 端点 `/api/image-proxy?url=xxx`，后端用 httpx 请求图片并返回 base64
- 优点：前端实现简单，绕过跨域和 Referer 限制
- 缺点：增加服务器带宽消耗

**方案 B：直接加载**
- 在 `<img>` 标签中直接使用图片 URL
- 小红书图片 URL 没有 Referer 校验，可以直接跨域加载
- **实测可行**，推荐使用方案 B

### 6.4 Cookie 处理

- Cookie 为可选参数，不登录也能抓取大部分数据
- 登录后可以获取更高清的图片和更多数据
- 在前端设置面板中提供一个 Cookie 输入框
- Cookie 获取方式：浏览器 F12 → Application → Cookies → 复制所有 Cookie 字符串

### 6.5 下载目录配置

```json
// settings.json
{
  "download_dir": "/home/user/xiaohongshu-images",
  "image_format": "jpeg",
  "folder_mode": false,
  "author_archive": true,
  "cookie": ""
}
```

- `download_dir`：文件保存根目录
- `image_format`：图片格式（jpeg / png / webp / auto）
- `folder_mode`：是否每个帖子创建单独文件夹
- `author_archive`：是否按作者分文件夹
- `cookie`：全局 Cookie（可被前端覆盖）

### 6.6 下载进度反馈

由于 `XHS.extract()` 是同步阻塞的（async 但内部没有进度回调），下载进度反馈有两种方案：

**方案 A：轮询（简单）**
- 下载完成后一次性返回所有结果
- 前端显示"下载中..."并等待

**方案 B：SSE / WebSocket（体验好）**
- 后端使用 SSE 流式推送下载进度
- 需要修改或包装 `Download` 类
- 推荐使用方案 A 先实现基础功能，后续迭代方案 B

---

## 七、部署方案

### 7.1 方式一：直接运行（推荐用于开发/简单部署）

```bash
# 1. 安装 Python 3.12+
# 2. 安装依赖
cd XHS-Downloader
pip install -r requirements.txt

# 3. 进入 web-app 目录
cd ../web-app
pip install fastapi uvicorn aiofiles

# 4. 启动服务
python main.py
# 或者
uvicorn server:app --host 0.0.0.0 --port 8080
```

### 7.2 方式二：Docker 部署

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装依赖
COPY XHS-Downloader/requirements.txt /app/base-requirements.txt
RUN pip install --no-cache-dir -r /app/base-requirements.txt

COPY web-app/requirements.txt /app/web-requirements.txt
RUN pip install --no-cache-dir -r /app/web-requirements.txt

# 复制代码
COPY XHS-Downloader/source /app/XHS-Downloader/source
COPY web-app /app/web-app

# 创建下载目录
RUN mkdir -p /data/downloads

EXPOSE 8080

CMD ["python", "/app/web-app/main.py"]
```

### 7.3 方式三：systemd 服务（推荐用于生产）

```ini
# /etc/systemd/system/xhs-downloader.service
[Unit]
Description=小红书图片下载 Web 服务
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/xhs-downloader/web-app
ExecStart=/usr/bin/python3 /opt/xhs-downloader/web-app/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now xhs-downloader.service
```

---

## 八、开发步骤（建议顺序）

### 第 1 步：搭建基础项目结构
- 创建 `web-app/` 目录
- 创建 `main.py`、`server.py`、`config.py`
- 设置 `sys.path` 使现有 `source/` 可导入

### 第 2 步：实现后端 API
- `POST /api/parse` — 解析链接，返回帖子数据
- `POST /api/download` — 下载图片
- 测试：用 curl 或 FastAPI 自带 Swagger UI 测试

### 第 3 步：编写前端页面
- `index.html` — 页面结构
- `style.css` — 样式（响应式、卡片布局）
- `app.js` — 交互逻辑（调 API、渲染结果、选择图片）

### 第 4 步：联调测试
- 用真实小红书链接测试完整流程
- 处理错误情况（无效链接、网络超时、下载失败）

### 第 5 步：配置与部署
- 配置下载目录
- 编写 Dockerfile
- 编写 systemd service 文件
- 部署到 Linux 服务器

### 第 6 步（可选）：增强功能
- 下载进度实时推送（SSE）
- 支持视频下载
- 批量链接输入
- 下载历史记录查询
- 暗色模式

---

## 九、关键代码参考

### 9.1 现有项目中可复用的类和函数

| 类/函数 | 位置 | 用途 |
|---------|------|------|
| `XHS` | `source.application.app` | 主类，`extract(url, download, index)` |
| `Settings` | `source.module.settings` | 配置管理，`run()` 返回配置 dict |
| `Download` | `source.application.download` | 文件下载逻辑 |
| `Image.get_image_link()` | `source.application.image` | 从 HTML 数据中提取图片下载 URL |
| `Explore.run()` | `source.application.explore` | 从 HTML 命名空间提取帖子结构化数据 |
| `Html.request_url()` | `source.application.request` | 发送 HTTP 请求获取小红书页面 |
| `Manager` | `source.module.manager` | 全局配置和 HTTP 客户端管理 |
| `Namespace` | `source.expansion.namespace` | 安全地从嵌套数据中提取字段 |
| `Cleaner.filter_name()` | `source.expansion.cleaner` | 清理文件名中的非法字符 |

### 9.2 最简调用示例

```python
import sys
sys.path.insert(0, "/path/to/XHS-Downloader")

from asyncio import run
from source import XHS, Settings

async def main():
    settings = Settings().run()
    settings["work_path"] = "/data/downloads"
    settings["image_format"] = "jpeg"
    
    async with XHS(**settings) as xhs:
        # 仅解析，不下载
        data = await xhs.extract(
            "https://www.xiaohongshu.com/explore/xxxxx",
            download=False,
        )
        print(data)  # 返回帖子信息
        
        # 下载第1、3、5张图片
        data = await xhs.extract(
            "https://www.xiaohongshu.com/explore/xxxxx",
            download=True,
            index=[1, 3, 5],
        )

run(main())
```

### 9.3 XHS.extract() 返回的数据结构

```python
[{
    "作品ID": "67890abcd",
    "作品链接": "https://www.xiaohongshu.com/explore/67890abcd",
    "作品标题": "今日穿搭分享",
    "作品描述": "一些描述文字...",
    "作品类型": "图文",           # "图文" | "视频" | "图集"
    "作品标签": "穿搭 OOTD",
    "作者昵称": "时尚博主小红",
    "作者ID": "5fxxxxx",
    "作者链接": "https://www.xiaohongshu.com/user/profile/5fxxxxx",
    "发布时间": "2025-06-01_12:30:00",
    "最后更新时间": "2025-06-01_12:30:00",
    "收藏数量": "200",
    "评论数量": "50",
    "分享数量": "30",
    "点赞数量": "1500",
    "下载地址": [               # 图片/视频的下载 URL 列表
        "https://ci.xiaohongshu.com/abc123?imageView2/format/jpeg",
        "https://ci.xiaohongshu.com/def456?imageView2/format/jpeg",
    ],
    "动图地址": [               # 动图 URL（如果有的话）
        null,
        "https://...mp4",
    ],
    "时间戳": 1717255800.0,
}]
```

---

## 十、注意事项

1. **Python 版本**：必须 >= 3.12（现有项目使用了泛型语法等特性）
2. **网络环境**：小红书服务器在中国大陆，服务器需要有访问国内网络的能力
3. **反爬虫**：频繁请求可能被限流，建议添加请求间隔
4. **Cookie 非必需**：不登录也能下载大部分图片，但登录后可能获得更高质量的图片
5. **图片格式**：小红书原始图片为 WEBP 格式，可通过 URL 参数转换为 PNG/JPEG/HEIC
6. **视频文件**：视频文件较大，如需支持视频下载需要额外处理
7. **短链接**：`xhslink.com` 短链需要先重定向解析，现有代码已处理

---

## 十一、配置文件示例

### web-app/settings.json
```json
{
  "download_dir": "./downloads",
  "image_format": "jpeg",
  "folder_mode": false,
  "author_archive": true,
  "cookie": "",
  "server_host": "0.0.0.0",
  "server_port": 8080
}
```

---

## 总结

这个方案的核心思路是 **复用 > 重写**。现有 XHS-Downloader 项目已经解决了小红书数据抓取的所有技术难点，我们只需要：

1. 写一个 FastAPI Web 服务（约 100 行）
2. 写一个简单的 HTML/CSS/JS 前端（约 300 行）
3. 配置下载目录和启动方式

总计代码量预计 **400-500 行**，开发时间约 **2-4 小时**。
