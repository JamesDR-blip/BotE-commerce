"""FastAPI application factory."""
from __future__ import annotations
from io import BytesIO
import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from api.schemas import ValidationResponse
from configs.settings import Settings
from services.container import Container
from services.logging import configure_logging, instrument_fastapi
from services.quality_service import QualityService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings(); configure_logging(settings.log_level)
    container = Container(settings); service = QualityService(container)
    app = FastAPI(title="AI Data Quality Platform", version="1.0.0")
    @app.get("/health")
    def health() -> dict[str, str]: return {"status": "ok"}
    @app.get("/categories")
    def categories() -> dict[str, list[str]]: return {"categories": container.registry.categories()}
    @app.get("/executions")
    def history(limit: int = 50) -> list[dict]:
        return [{"id": x.id, "category": x.category, "health_score": x.health_score, "created_at": x.created_at.isoformat()} for x in container.executions.history(min(max(limit, 1), 100))]
    @app.post("/validations", response_model=ValidationResponse)
    async def validate(file: UploadFile = File(...), category: str | None = Form(None)) -> ValidationResponse:
        content = await file.read()
        try:
            frame = pd.read_csv(BytesIO(content)) if (file.filename or "").lower().endswith(".csv") else pd.read_excel(BytesIO(content))
            if frame.empty: raise ValueError("Input has no records")
            result = service.validate(frame, content, category)
            return ValidationResponse(execution_id=result.execution_id, category=result.category, health_score=result.health_score, reports=result.report_paths, cached=result.cached)
        except (ValueError, KeyError) as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    instrument_fastapi(app)
    return app
