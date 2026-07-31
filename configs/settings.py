"""Typed configuration loaded from environment variables."""
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings; no configuration is kept in module globals."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///./data_quality.db"
    rules_path: Path = Path("rules_library.yaml")
    validators_path: Path = Path("validators")
    reports_path: Path = Path("artifacts/reports")
    cache_ttl_seconds: int = Field(default=3600, ge=0)
    max_upload_bytes: int = Field(default=25 * 1024 * 1024, gt=0)
    enable_llm: bool = False
    google_api_key: str | None = None
    llm_model: str = "gemini-2.5-flash"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    api_base_url: str = "http://127.0.0.1:8000"
