import json
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
        self.config_path = (
            Path(config_path)
            if config_path
            else Path(__file__).parent / "settings.json"
        )

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
