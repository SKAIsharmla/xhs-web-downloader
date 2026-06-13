# ======================================================================
# 小红书图片下载器 — Docker image
#
# Build:
#   cd 小红书下载
#   docker build -f web-app/Dockerfile -t xhs-web-downloader .
#
# Run:
#   docker run -d \
#     --name xhs-downloader \
#     -p 8080:8080 \
#     -v /path/to/downloads:/app/web-app/downloads \
#     -v /path/to/settings.json:/app/web-app/settings.json \
#     xhs-web-downloader
# ======================================================================

FROM python:3.12-slim

LABEL name="XHS-Web-Downloader" \
      description="小红书图片下载 Web 工具" \
      version="1.0.0"

WORKDIR /app

# ---- Install system dependencies (for curl-cffi etc.) ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ---- Copy XHS-Downloader (source + locale) ----
COPY XHS-Downloader/source  /app/XHS-Downloader/source
COPY XHS-Downloader/locale  /app/XHS-Downloader/locale

# ---- Install all Python dependencies from pyproject.toml ----
# This installs the `source` package to site-packages (so imports work)
# AND all its dependencies (curl-cffi, httpx, fastapi, etc.)
COPY XHS-Downloader/pyproject.toml /app/XHS-Downloader/
RUN pip install --no-cache-dir /app/XHS-Downloader/

# ---- Copy web-app ----
COPY web-app /app/web-app

# ---- Runtime config ----
WORKDIR /app/web-app

# PYTHONPATH ensures locale files are found at the original path
ENV PYTHONPATH=/app/XHS-Downloader:$PYTHONPATH

RUN mkdir -p /app/web-app/downloads

EXPOSE 8080

VOLUME ["/app/web-app/downloads"]

CMD ["python", "main.py"]
