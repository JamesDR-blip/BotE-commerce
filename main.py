"""Local entry point for the Data Quality Platform API."""
from __future__ import annotations

import uvicorn

from api.main import create_app
from configs.settings import Settings


if __name__ == "__main__":
    settings = Settings()
    uvicorn.run(create_app(), host=settings.host, port=settings.port)
