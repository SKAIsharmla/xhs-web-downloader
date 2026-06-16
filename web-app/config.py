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

import json
from os import environ
from pathlib import Path


class WebConfig:
    """Web application configuration management."""

    DEFAULTS = {
        "download_dir": "./downloads",
        "image_format": "jpeg",
        "folder_mode": False,
        "author_archive": True,
        "cookie": "",
        "server_host": "0.0.0.0",
        "server_port": 8080,
    }

    def __init__(self, config_path: str | Path | None = None):
        # Priority: explicit path > env var XHS_CONFIG_PATH > default ./settings.json
        if config_path is None:
            config_path = environ.get(
                "XHS_CONFIG_PATH",
                str(Path(__file__).parent / "settings.json"),
            )
        self.config_path = Path(config_path)

    def load(self) -> dict:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return self.DEFAULTS | json.load(f)
        return self.DEFAULTS.copy()

    def save(self, data: dict) -> dict:
        current = self.load()
        current.update({k: v for k, v in data.items() if v is not None})
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
        return current
