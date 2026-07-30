"""Backward-compatible API entry point.

The executable application entry point lives in :mod:`app.main`.
"""
from app.main import create_app

__all__ = ["create_app"]


if __name__ == "__main__":
    import uvicorn

    from configs.settings import Settings

    settings = Settings()
    uvicorn.run(create_app(), host=settings.host, port=settings.port)
