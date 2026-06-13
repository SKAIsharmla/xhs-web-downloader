# 小红书图片下载器 Web版

> 基于 [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader) 核心引擎的 Web 图形界面工具。在局域网 Linux 服务器上部署，通过浏览器访问即可下载小红书无水印图片。

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

## 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 进入项目目录的 web-app 子目录
cd web-app

# 启动（后台运行）
docker compose up -d

# 查看日志
docker compose logs -f

# 访问 http://你的服务器IP:8080
```

> 首次启动会自动下载依赖并构建镜像，耗时 1-3 分钟。

### 方式二：直接运行

```bash
# 要求 Python 3.12+
cd web-app

# 安装依赖
pip install -r ../XHS-Downloader/requirements.txt

# 启动
python main.py
```

启动后浏览器访问 `http://服务器IP:8080`。

---

## 使用说明

### 第一步：解析链接

1. 打开浏览器访问 `http://服务器IP:8080`
2. 复制小红书帖子链接，粘贴到输入框
3. 点击 **解析** 按钮

支持的链接格式：
- `https://www.xiaohongshu.com/explore/65d9c2a0000000001a012345`
- `https://www.xiaohongshu.com/discovery/item/65d9c2a0000000001a012345`
- `https://xhslink.com/ABCDEF`

### 第二步：选择图片

解析成功后可以看到：
- 帖子标题、作者、发布时间
- 所有图片的缩略图网格
- 每张图片右上角有选中标记

点击图片可以切换选中状态，顶部工具栏支持全选/取消全选。

### 第三步：下载

点击 **下载选中图片** 按钮，图片会自动保存到服务器上配置的目录中。下载完成后页面会显示结果。

### 设置

点击右上角 **⚙ 设置** 按钮，可以修改：

| 设置项 | 说明 | 默认值 |
|--------|------|--------|
| 下载目录 | 服务器上保存图片的路径 | `./downloads` |
| 图片格式 | JPEG / PNG / WEBP / 原始格式 | JPEG |
| 按作者归档 | 每个作者的图片存到单独子文件夹 | 开启 |
| Cookie | 登录态 Cookie（可选，参见下方说明） | 空 |

#### 关于 Cookie

Cookie 是**可选参数**。不填 Cookie 也能正常下载大部分图片。
如果需要获取更完整的数据（如高清原图），可以填写登录后的 Cookie：

1. 浏览器打开 [xiaohongshu.com](https://www.xiaohongshu.com) 并登录
2. 按 F12 打开开发者工具 → Application → Cookies
3. 复制所有 Cookie 字符串，粘贴到设置中

---

## 配置文件

`settings.json` 文件内容说明：

```json
{
  "download_dir": "./downloads",    // 下载保存路径
  "image_format": "jpeg",           // 图片格式：jpeg/png/webp/auto
  "folder_mode": false,             // 每个帖子单独文件夹
  "author_archive": true,           // 按作者分文件夹
  "cookie": "",                     // 全局 Cookie（可在网页上覆盖）
  "server_host": "0.0.0.0",         // 监听地址
  "server_port": 8080               // 监听端口
}
```

> 修改配置后无需重启，在网页设置面板保存即可生效。

---

## 项目结构

```
web-app/
├── main.py              # 启动入口
├── server.py            # FastAPI 后端（API + 静态文件）
├── config.py            # 配置管理
├── settings.json        # 配置文件
├── Dockerfile           # Docker 构建文件
├── docker-compose.yml   # Docker Compose 配置
├── downloads/           # 默认下载目录
└── frontend/            # 前端页面
    ├── index.html       # 页面结构
    ├── style.css        # 样式
    └── app.js           # 交互逻辑
```

### 依赖的核心库

本项目不重复造轮子，核心爬取和下载能力来自 [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader)：

| 模块 | 来源 | 功能 |
|------|------|------|
| `source.application.app.XHS` | XHS-Downloader | 主类：链接解析、数据提取、文件下载 |
| `source.application.download.Download` | XHS-Downloader | 文件下载（断点续传、签名校验） |
| `source.application.image.Image` | XHS-Downloader | 图片下载地址提取 |
| `source.application.explore.Explore` | XHS-Downloader | 帖子结构化数据解析 |

---

## 部署到局域网 Linux 服务器

### 网络要求

服务器需要有访问国内网络的能力（xiaohongshu.com 服务器在中国大陆）。

### 端口放行

确保服务器的防火墙允许 8080 端口：

```bash
# 如果使用 firewalld
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --reload

# 如果使用 ufw
ufw allow 8080
```

### Docker 部署详细步骤

```bash
# 1. 安装 Docker 和 Docker Compose（如果未安装）
# 2. 将项目传到服务器
git clone 你的仓库地址 /opt/xhs-downloader

# 3. 创建数据目录
mkdir -p /data/xhs-downloads

# 4. 修改 docker-compose.yml 中的 volumes 路径
#    ./downloads -> /data/xhs-downloads

# 5. 启动
cd /opt/xhs-downloader/web-app
docker compose up -d

# 6. 验证
curl http://localhost:8080/api/settings
```

### 使用 systemd 管理（非 Docker 方式）

```ini
# /etc/systemd/system/xhs-downloader.service
[Unit]
Description=小红书图片下载器
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/xhs-downloader/web-app
ExecStart=/usr/bin/python3 /opt/xhs-downloader/web-app/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now xhs-downloader.service
```

---

## 常见问题

**Q: 解析失败，提示"提取小红书作品链接失败"？**

检查链接格式是否正确，确保是完整的小红书帖子链接。短链接（xhslink.com）也支持。

**Q: 图片加载不出来？**

图片通过 `Web Proxy` 方式加载，服务端自动处理了防盗链问题。如仍有问题，检查服务器是否能正常访问 ci.xiaohongshu.com。

**Q: 下载的图片在哪里？**

默认保存在 `web-app/downloads/` 目录下（按作者分文件夹）。可以在设置页面修改下载目录。

**Q: 可以下载视频吗？**

当前版本专注于图片下载。视频下载需要额外处理（文件较大），后续可考虑支持。

**Q: Cookie 过期了怎么办？**

重新从浏览器复制 Cookie，在设置页面更新即可。

---

## License

GNU General Public License v3.0

本项目基于 [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader)（GPL-3.0），感谢原作者 [JoeanAmier](https://github.com/JoeanAmier) 的卓越工作。
