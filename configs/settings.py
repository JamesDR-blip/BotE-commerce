"""Typed configuration loaded from environment variables."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings; no configuration is kept in module globals."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./data_quality.db"
    rules_path: Path = Path("rules_library.yaml")
    validators_path: Path = Path("validators")
    reports_path: Path = Path("artifacts/reports")
    cache_ttl_seconds: int = 3600
    max_upload_bytes: int = 25 * 1024 * 1024
    enable_llm: bool = False
    google_api_key: str | None = None
    llm_model: str = "gemini-2.5-flash"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000
