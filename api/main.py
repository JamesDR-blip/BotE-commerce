"""FastAPI application factory."""
from __future__ import annotations
import logging
from pathlib import Path
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from domain.exceptions import ValidationRequestError
from api.dependencies import get_container, get_data_operations, get_mapping_service, get_quality_service
from schemas.responses import ExtractionResponse, HistoryResponse, MappingResponse, TabularPreviewResponse, UploadResponse, ValidationResponse
from configs.settings import Settings
from services.container import Container
from services.logging import configure_logging, instrument_fastapi
from services.quality_service import QualityService
from services.data_operations import DataOperationsService
from services.mapping_service import MappingService

logger = logging.getLogger(__name__)


def _internal_server_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unexpected_application_error",
        extra={
            "event": "unexpected_application_error",
        },
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.log_level)
    logger.info("application_configured", extra={"event": "application_configured", "environment": settings.environment})
    container = Container(settings); service = QualityService(container)
    app = FastAPI(title="AI Data Quality Platform", version="1.0.0")
    app.add_exception_handler(Exception, _internal_server_error)
    app.state.container = container
    app.state.quality_service = service
    app.state.data_operations = container.data_operations
    app.state.mapping_service = container.mapping
    @app.get("/health")
    def health() -> dict[str, str]: return {"status": "ok"}
    @app.get("/categories")
    def categories(current: Container = Depends(get_container)) -> dict[str, list[str]]: return {"categories": current.registry.categories()}
    @app.get("/executions")
    def history(limit: int = 50, current: Container = Depends(get_container)) -> list[dict[str, str | float]]:
        return _history_items(current, limit)
    @app.get("/history", response_model=HistoryResponse)
    def history_alias(limit: int = 50, current: Container = Depends(get_container)) -> HistoryResponse:
        return HistoryResponse(items=_history_items(current, limit))
    @app.get("/executions/{execution_id}/reports/{report_format}")
    def download_report(execution_id: str, report_format: str, current: Container = Depends(get_container)) -> FileResponse:
        return _download_report(current, execution_id, report_format)
    @app.get("/report/{execution_id}/{report_format}")
    def report_alias(execution_id: str, report_format: str, current: Container = Depends(get_container)) -> FileResponse:
        return _download_report(current, execution_id, report_format)
    @app.post("/upload", response_model=UploadResponse)
    async def upload(file: UploadFile = File(...), current: Container = Depends(get_container)) -> UploadResponse:
        frame = await _read_frame(file, current)
        return UploadResponse(filename=file.filename or "", rows=len(frame), columns=[str(column) for column in frame.columns])
    @app.post("/clean", response_model=TabularPreviewResponse)
    async def clean(file: UploadFile = File(...), category: str | None = Form(None), operations: DataOperationsService = Depends(get_data_operations), current: Container = Depends(get_container)) -> TabularPreviewResponse:
        frame = await _read_frame(file, current)
        detected, cleaned = operations.clean(frame, category)
        return _preview(detected, cleaned)
    @app.post("/extract", response_model=ExtractionResponse)
    async def extract(file: UploadFile = File(...), operations: DataOperationsService = Depends(get_data_operations), current: Container = Depends(get_container)) -> ExtractionResponse:
        frame = await _read_frame(file, current)
        return ExtractionResponse(records=[{"row": index + 2, "attributes": item.as_dict()} for index, item in enumerate(operations.extract(frame))])
    @app.post("/mapping", response_model=MappingResponse)
    async def mapping(file: UploadFile = File(...), target_columns: str | None = Form(None), mappings: MappingService = Depends(get_mapping_service), current: Container = Depends(get_container)) -> MappingResponse:
        frame = await _read_frame(file, current)
        targets = [value.strip() for value in target_columns.split(",") if value.strip()] if target_columns else None
        suggested, unmapped = mappings.suggest(frame.columns, targets)
        return MappingResponse(mappings=suggested, unmapped_columns=unmapped)
    @app.post("/validate", response_model=ValidationResponse)
    async def validate_alias(file: UploadFile = File(...), category: str | None = Form(None), current: Container = Depends(get_container), quality: QualityService = Depends(get_quality_service)) -> ValidationResponse:
        return await _validate_upload(file, category, current, quality)
    @app.post("/validations", response_model=ValidationResponse)
    async def validate(file: UploadFile = File(...), category: str | None = Form(None), current: Container = Depends(get_container), quality: QualityService = Depends(get_quality_service)) -> ValidationResponse:
        return await _validate_upload(file, category, current, quality)
    instrument_fastapi(app)
    return app


async def _read_frame(file: UploadFile, container: Container):
    try:
        return container.uploads.read(file.filename, await file.read())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


async def _validate_upload(file: UploadFile, category: str | None, container: Container, service: QualityService) -> ValidationResponse:
    content = await file.read()
    try:
        logger.info("validation_requested", extra={"event": "validation_requested", "upload_filename": file.filename, "requested_category": category})
        frame = container.uploads.read(file.filename, content)
        result = service.validate(frame, content, category)
        urls = {name: f"/executions/{result.execution_id}/reports/{name}" for name in result.report_paths}
        logger.info("validation_completed", extra={"event": "validation_completed", "execution_id": result.execution_id, "category": result.category, "cached": result.cached})
        return ValidationResponse(execution_id=result.execution_id, category=result.category, health_score=result.health_score, reports=urls, cached=result.cached)
    except ValidationRequestError as exc:
        logger.warning("validation_rejected", extra={"event": "validation_rejected", "upload_filename": file.filename, "reason": str(exc)})
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(
            "validation_unexpected_error",
            extra={
                "event": "validation_unexpected_error",
                "upload_filename": file.filename,
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        raise


def _preview(category: str, frame) -> TabularPreviewResponse:
    return TabularPreviewResponse(category=category, rows=len(frame), columns=[str(column) for column in frame.columns], records=frame.head(100).to_dict(orient="records"))


def _history_items(container: Container, limit: int) -> list[dict[str, str | float]]:
    return [{"id": item.id, "category": item.category, "health_score": item.health_score, "created_at": item.created_at.isoformat()} for item in container.executions.history(min(max(limit, 1), 100))]


def _download_report(container: Container, execution_id: str, report_format: str) -> FileResponse:
    if report_format not in {"excel", "html", "pdf", "json"}:
        raise HTTPException(status_code=404, detail="Unsupported report format")
    path = container.executions.report_path(execution_id, report_format)
    if not path or not Path(path).is_file():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(path, filename=f"data-quality-report.{Path(path).suffix.lstrip('.')}")
