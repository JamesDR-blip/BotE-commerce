"""Backward-compatible import for observability infrastructure."""
from infrastructure.observability.logging import (
    JsonFormatter,
    configure_logging,
    instrument_fastapi,
)

__all__ = ["JsonFormatter", "configure_logging", "instrument_fastapi"]
