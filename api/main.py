"""FastAPI application factory."""
from __future__ import annotations
import logging
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from schemas.responses import ValidationResponse
from configs.settings import Settings
from services.container import Container
from services.logging import configure_logging, instrument_fastapi
from services.quality_service import QualityService

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.log_level)
    logger.info("application_configured", extra={"event": "application_configured", "environment": settings.environment})
    container = Container(settings); service = QualityService(container)
    app = FastAPI(title="AI Data Quality Platform", version="1.0.0")
    @app.get("/health")
    def health() -> dict[str, str]: return {"status": "ok"}
    @app.get("/categories")
    def categories() -> dict[str, list[str]]: return {"categories": container.registry.categories()}
    @app.get("/executions")
    def history(limit: int = 50) -> list[dict[str, str | float]]:
        return [{"id": x.id, "category": x.category, "health_score": x.health_score, "created_at": x.created_at.isoformat()} for x in container.executions.history(min(max(limit, 1), 100))]
    @app.get("/executions/{execution_id}/reports/{report_format}")
    def download_report(execution_id: str, report_format: str) -> FileResponse:
        if report_format not in {"excel", "html", "pdf", "json"}:
            raise HTTPException(status_code=404, detail="Unsupported report format")
        path = container.executions.report_path(execution_id, report_format)
        if not path or not Path(path).is_file():
            raise HTTPException(status_code=404, detail="Report not found")
        return FileResponse(path, filename=f"data-quality-report.{Path(path).suffix.lstrip('.')}")
    @app.post("/validations", response_model=ValidationResponse)
    async def validate(file: UploadFile = File(...), category: str | None = Form(None)) -> ValidationResponse:
        content = await file.read()
        try:
            logger.info("validation_requested", extra={"event": "validation_requested", "filename": file.filename, "requested_category": category})
            frame = container.uploads.read(file.filename, content)
            result = service.validate(frame, content, category)
            urls = {name: f"/executions/{result.execution_id}/reports/{name}" for name in result.report_paths}
            logger.info("validation_completed", extra={"event": "validation_completed", "execution_id": result.execution_id, "category": result.category, "cached": result.cached})
            return ValidationResponse(execution_id=result.execution_id, category=result.category, health_score=result.health_score, reports=urls, cached=result.cached)
        except (ValueError, KeyError) as exc:
            logger.warning("validation_rejected", extra={"event": "validation_rejected", "filename": file.filename, "reason": str(exc)})
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    instrument_fastapi(app)
    return app
