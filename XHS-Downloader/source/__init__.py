from .application import XHS
from .module import Settings

# CLI 和 TUI 使用懒导入，避免未安装相关依赖时出错
def __getattr__(name):
    if name == "XHSDownloader":
        from .TUI import XHSDownloader as _XHSDownloader
        return _XHSDownloader
    if name == "cli":
        from .CLI import cli as _cli
        return _cli
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "XHS",
    "XHSDownloader",
    "cli",
    "Settings",
]
