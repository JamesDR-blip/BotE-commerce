"""Structured JSON logging and optional OpenTelemetry instrumentation."""
from __future__ import annotations
import json
import logging
from typing import Any


_HANDLER_NAME = "ai_data_studio_json"
_STANDARD_RECORD_ATTRIBUTES = frozenset(logging.makeLogRecord({}).__dict__)


class JsonFormatter(logging.Formatter):
    """Render log records as JSON without relying on a logging provider."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(
            {
                key: value
                for key, value in record.__dict__.items()
                if key not in _STANDARD_RECORD_ATTRIBUTES and not key.startswith("_")
            }
        )
        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging(level: str) -> None:
    """Configure one idempotent JSON handler for the application root logger."""
    root = logging.getLogger()
    root.setLevel(level.upper())
    if any(handler.get_name() == _HANDLER_NAME for handler in root.handlers):
        return
    handler = logging.StreamHandler()
    handler.set_name(_HANDLER_NAME)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)


def instrument_fastapi(app: object) -> None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)  # type: ignore[arg-type]
    except ImportError:
        logging.getLogger(__name__).warning("OpenTelemetry instrumentation unavailable")
