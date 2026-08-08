"""Application entry point."""

from __future__ import annotations

import uvicorn

from api.main import create_app
from configs.settings import Settings
from services.logging import configure_logging

# ------------------------------------------------------------------
# Bootstrap
# ------------------------------------------------------------------

settings = Settings()

configure_logging(settings.log_level)

# ------------------------------------------------------------------
# FastAPI Application
# ------------------------------------------------------------------

app = create_app(settings)

# ------------------------------------------------------------------
# Local Development
# ------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=False,
    )