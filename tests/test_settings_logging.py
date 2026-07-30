import json
import logging

from configs.settings import Settings
from services.logging import JsonFormatter


def test_settings_reads_environment_values(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "2048")
    settings = Settings(_env_file=None)
    assert settings.environment == "test"
    assert settings.max_upload_bytes == 2048


def test_json_formatter_includes_structured_extra_fields() -> None:
    record = logging.makeLogRecord({"name": "test", "levelno": logging.INFO, "levelname": "INFO", "msg": "completed", "args": (), "event": "validation_completed", "execution_id": "abc"})
    payload = json.loads(JsonFormatter().format(record))
    assert payload["event"] == "validation_completed"
    assert payload["execution_id"] == "abc"
