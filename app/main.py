"""Local entry point for the Data Quality Platform API."""
from __future__ import annotations

import uvicorn

from api.main import create_app
from configs.settings import Settings
from services.logging import configure_logging


if __name__ == "__main__":
    settings = Settings()
    configure_logging(settings.log_level)
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port)
