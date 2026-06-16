# 小红书图片下载器 Web版

> **修改声明**：本项目基于 [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader)（GPL-3.0）进行了修改，为其添加了 Web 图形界面（FastAPI + 前端）、Docker 容器化部署和设置管理功能。修改时间：2026 年。  
> 修改者：[SKAIsharmla](https://github.com/SKAIsharmla)

本目录是 Web 界面子项目，完整说明请查看根目录 [README.md](../README.md)。

## 本地开发

```bash
# 要求 Python 3.12+
pip install -r ../XHS-Downloader/requirements.txt
python main.py
```

启动后浏览器访问 `http://localhost:8080`。

## Docker 构建

```bash
# 在项目根目录执行
docker build -f web-app/Dockerfile -t xhs-web-downloader .
```

或直接使用 Docker Hub 镜像：

```bash
docker pull yukikaze0/xhs-web-downloader:latest
```

## 项目结构

```
web-app/
├── main.py              # 启动入口
├── server.py            # FastAPI 后端（API + 静态文件）
├── config.py            # 配置管理
├── settings.json        # 配置文件
├── Dockerfile           # Docker 构建文件
├── docker-compose.yml   # Docker Compose 配置
├── entrypoint.sh        # 容器启动脚本
└── frontend/            # 前端页面
    ├── index.html       # 页面结构
    ├── style.css        # 样式
    └── app.js           # 交互逻辑
```

## License

GNU General Public License v3.0

本项目基于 [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader)（GPL-3.0），感谢原作者 [JoeanAmier](https://github.com/JoeanAmier) 的卓越工作。
