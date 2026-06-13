import uvicorn

from config import WebConfig

if __name__ == "__main__":
    cfg = WebConfig().load()
    uvicorn.run(
        "server:app",
        host=cfg.get("server_host", "0.0.0.0"),
        port=cfg.get("server_port", 8080),
        reload=False,
        log_level="info",
    )
