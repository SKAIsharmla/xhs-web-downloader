# 小红书图片下载器 Web版

> **修改声明**：本项目基于 [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader)（GPL-3.0）进行了修改，为其添加了 Web 图形界面（FastAPI + 前端）、Docker 容器化部署和设置管理功能。修改时间：2025 年。  
> 修改者：[SKAIsharmla](https://github.com/SKAIsharmla)

基于 XHS-Downloader 核心引擎的 Web 图形界面工具。在 NAS 或 Linux 服务器上部署，通过浏览器访问即可下载小红书无水印图片。

![](https://img.shields.io/badge/Python-3.12+-blue)
![](https://img.shields.io/badge/FastAPI-0.136-green)
![](https://img.shields.io/badge/license-GPL--3.0-red)

---

## 功能

| 功能 | 说明 |
|------|------|
| 🔗 **链接解析** | 支持 `/explore/`、`/discovery/item/`、`xhslink.com` 短链接 |
| 🖼 **图片预览** | 解析后展示所有图片缩略图，支持勾选/全选 |
| ⬇ **选择性下载** | 只下载你勾选的图片，保存到服务器指定目录 |
| ⚙ **网页配置** | 下载目录、图片格式（JPEG/PNG/WEBP）、按作者归档，都在网页上设置 |
| 🐳 **Docker 部署** | 一条命令启动，下载目录持久化 |

---

## 快速开始（Docker）

从 Docker Hub 直接拉取镜像：

```bash
docker pull yukikaze0/xhs-web-downloader:latest
```

### 运行容器

```bash
docker run -d \
  --name xhs-downloader \
  --restart unless-stopped \
  -p 8080:8080 \
  -v /path/to/downloads:/data/downloads \
  -v xhs-config:/data/config \
  yukikaze0/xhs-web-downloader:latest
```

**卷挂载说明：**

| 挂载 | 用途 | 说明 |
|------|------|------|
| `-v /path/to/downloads:/data/downloads` | 下载目录 | **必选**，下载的图片保存在这里 |
| `-v xhs-config:/data/config` | 配置持久化 | **推荐**，Web 页面修改的设置（Cookie、图片格式等）会保存在这个卷中，容器删除重建后不丢失。不挂载则设置存在容器内部，删容器会恢复默认 |

> Docker 命名卷（如 `xhs-config`）会自动创建。如果希望配置文件直接放在宿主机目录，可以用 `-v /path/to/config:/data/config`。

### 查看日志

```bash
docker logs xhs-downloader
```

---

## Docker Compose

在 `web-app/` 目录下：

```yaml
services:
  xhs-downloader:
    image: yukikaze0/xhs-web-downloader:latest
    container_name: xhs-downloader
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./downloads:/data/downloads
      - xhs-config:/data/config

volumes:
  xhs-config:
```

```bash
docker compose up -d
```

---

## 使用说明

### 1. 解析链接

打开浏览器访问 `http://你的服务器IP:8080`，粘贴小红书帖子链接，点击 **解析**。

支持的链接格式：
- `https://www.xiaohongshu.com/explore/65d9c2a0000000001a012345`
- `https://www.xiaohongshu.com/discovery/item/65d9c2a0000000001a012345`
- `https://xhslink.com/ABCDEF`

### 2. 选择图片下载

解析成功后可以看到所有图片缩略图，勾选需要的图片，点击 **下载选中图片**。

### 设置

点击右上角 **⚙ 设置** 按钮修改：

| 设置项 | 说明 | 默认值 |
|--------|------|--------|
| 下载目录 | 服务器上保存图片的路径 | `/data/downloads`（Docker） |
| 图片格式 | JPEG / PNG / WEBP | JPEG |
| 按作者归档 | 每个作者的图片存到单独子文件夹 | 开启 |
| Cookie | 登录态 Cookie（可选） | 空 |

> Cookie 为可选。不填也能下载大部分图片，如需要更完整数据（如高清原图），可登录小红书后从浏览器开发者工具中复制 Cookie 填入。

---

## 直接运行（非 Docker）

```bash
# 要求 Python 3.12+
cd web-app
pip install -r ../XHS-Downloader/requirements.txt
python main.py
```

启动后浏览器访问 `http://服务器IP:8080`。

---

## 项目结构

```
├── web-app/
│   ├── main.py              # 启动入口
│   ├── server.py            # FastAPI 后端（API + 静态文件）
│   ├── config.py            # 配置管理
│   ├── Dockerfile           # Docker 构建文件
│   ├── docker-compose.yml   # Docker Compose 配置
│   ├── entrypoint.sh        # 容器启动脚本
│   └── frontend/            # 前端页面
├── XHS-Downloader/
│   ├── source/              # 核心引擎（XHS-Downloader）
│   └── locale/              # 翻译文件
├── LICENSE                  # GPL-3.0
└── .dockerignore
```

### 依赖的核心库

核心爬取和下载能力来自 [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader)（MIT → GPL-3.0）：

| 模块 | 功能 |
|------|------|
| `source.application.app.XHS` | 主类：链接解析、数据提取、文件下载 |
| `source.application.download.Download` | 文件下载（断点续传、签名校验） |
| `source.application.image.Image` | 图片下载地址提取 |
| `source.application.explore.Explore` | 帖子结构化数据解析 |

---

## 常见问题

**Q: 解析失败？**  
检查链接格式是否正确。短链接（xhslink.com）也支持。

**Q: 图片加载不出来？**  
服务端自动处理了防盗链问题。如仍有问题，检查服务器是否能正常访问 `ci.xiaohongshu.com`。

**Q: 下载的图片在哪里？**  
在 Docker 启动时 `-v` 挂载的目录下。

**Q: 可以下载视频吗？**  
当前版本专注于图片下载。

**Q: Cookie 过期了怎么办？**  
重新从浏览器复制 Cookie，在设置页面更新即可。

---

## License

GNU General Public License v3.0

本项目基于 [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader)（GPL-3.0），感谢原作者 [JoeanAmier](https://github.com/JoeanAmier) 的卓越工作。
