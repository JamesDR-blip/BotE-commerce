"""Structured JSON logging and optional OpenTelemetry instrumentation."""
from __future__ import annotations
import json, logging


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({"level": record.levelname, "message": record.getMessage(), "logger": record.name, "timestamp": self.formatTime(record)})


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(); handler.setFormatter(JsonFormatter())
    root = logging.getLogger(); root.handlers.clear(); root.addHandler(handler); root.setLevel(level.upper())


def instrument_fastapi(app: object) -> None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)  # type: ignore[arg-type]
    except ImportError:
        logging.getLogger(__name__).warning("OpenTelemetry instrumentation unavailable")
