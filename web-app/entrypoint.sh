#!/bin/bash
set -e

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

# ======================================================================
# 初始化数据目录和配置文件
# ======================================================================
# XHS_CONFIG_PATH 和 XHS_DOWNLOAD_DIR 由 Docker 环境变量提供
# 默认值已在 Dockerfile 中设为 /data/config/settings.json 和 /data/downloads

mkdir -p "$(dirname "$XHS_CONFIG_PATH")" "$XHS_DOWNLOAD_DIR"

if [ ! -f "$XHS_CONFIG_PATH" ]; then
  echo "初始化配置文件: $XHS_CONFIG_PATH"
  cat > "$XHS_CONFIG_PATH" << CONFIG
{
  "download_dir": "$XHS_DOWNLOAD_DIR",
  "image_format": "jpeg",
  "folder_mode": false,
  "author_archive": true,
  "cookie": "",
  "server_host": "0.0.0.0",
  "server_port": 8080
}
CONFIG
fi

exec python main.py
