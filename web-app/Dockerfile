# Copyright (C) 2025 SKAIsharmla
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ======================================================================
# 小红书图片下载器 — Docker image
#
# Build:
#   docker build -f web-app/Dockerfile -t xhs-web-downloader .
#
# Run:
#   docker run -d \
#     --name xhs-downloader \
#     -p 8080:8080 \
#     -v xhs-data:/data \
#     xhs-web-downloader
# ======================================================================

FROM python:3.12-slim

LABEL name="XHS-Web-Downloader" \
      description="小红书图片下载 Web 工具" \
      version="1.0.0"

WORKDIR /app

# ---- Install Python dependencies ----
# 只安装 web-app 实际需要的依赖，不安装 TUI(textual)、剪贴板(pyperclip)等无关包
COPY XHS-Downloader/pyproject.toml /app/XHS-Downloader/
RUN pip install --no-cache-dir \
    curl-cffi>=0.15.0 \
    httpx[http2,socks]>=0.28.1 \
    lxml>=6.1.0 \
    aiofiles>=25.1.0 \
    aiosqlite>=0.22.1 \
    emoji>=2.15.0 \
    pyyaml>=6.0.3 \
    fastapi>=0.136.3 \
    fastmcp>=3.3.1 \
    uvicorn>=0.48.0 \
    websockets>=16.0

# ---- Copy XHS-Downloader source (直接通过 PYTHONPATH 导入) ----
COPY XHS-Downloader/source  /app/XHS-Downloader/source
COPY XHS-Downloader/locale  /app/XHS-Downloader/locale

# ---- Copy web-app ----
COPY web-app /app/web-app

# ---- Runtime config ----
WORKDIR /app/web-app

ENV PYTHONPATH=/app/XHS-Downloader
ENV XHS_CONFIG_PATH=/data/config/settings.json
ENV XHS_DOWNLOAD_DIR=/data/downloads

EXPOSE 8080

ENTRYPOINT ["/app/web-app/entrypoint.sh"]
