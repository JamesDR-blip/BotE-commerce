"""Application runtime entry point."""

from __future__ import annotations

import uvicorn

from api.main import create_app
from configs.settings import Settings

settings = Settings()

app = create_app(settings)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=False,
    )