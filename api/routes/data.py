"""Data processing API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException

from api.dependencies import (
    get_data_operations,
    get_mapping_service,
    get_quality_service,
    get_upload_reader
)
from schemas.responses import (
    ExtractionResponse,
    MappingResponse,
    TabularPreviewResponse,
    UploadResponse,
    ValidationResponse,
)
from services.data_operations import DataOperationsService
from services.mapping_service import MappingService
from application.quality.quality_service import QualityService
from infrastructure.upload.tabular_reader import TabularUploadReader

from domain.exceptions import ValidationRequestError

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/upload", response_model=UploadResponse)
async def upload(
    file: UploadFile = File(...),
    reader: TabularUploadReader = Depends(get_upload_reader),
) -> UploadResponse:
    frame = await _read_frame(file, reader)
    return UploadResponse(filename=file.filename or "", rows=len(frame), columns=[str(column) for column in frame.columns])
@router.post("/clean", response_model=TabularPreviewResponse)
async def clean(
    file: UploadFile = File(...),
    category: str | None = Form(None),
    operations: DataOperationsService = Depends(get_data_operations),
    reader: TabularUploadReader = Depends(get_upload_reader),
) -> TabularPreviewResponse:
    frame = await _read_frame(file, reader)
    detected, cleaned = operations.clean(frame, category)
    return _preview(detected, cleaned)
@router.post("/extract", response_model=ExtractionResponse)
async def extract(
    file: UploadFile = File(...),
    operations: DataOperationsService = Depends(get_data_operations),
    reader: TabularUploadReader = Depends(get_upload_reader),
) -> ExtractionResponse:
    frame = await _read_frame(file, reader)
    return ExtractionResponse(records=[{"row": index + 2, "attributes": item.as_dict()} for index, item in enumerate(operations.extract(frame))])
@router.post("/mapping", response_model=MappingResponse)
async def mapping(
    file: UploadFile = File(...),
    target_columns: str | None = Form(None),
    mappings: MappingService = Depends(get_mapping_service),
    reader: TabularUploadReader = Depends(get_upload_reader),
) -> MappingResponse:
    frame = await _read_frame(file, reader)
    targets = [value.strip() for value in target_columns.split(",") if value.strip()] if target_columns else None
    suggested, unmapped = mappings.suggest(frame.columns, targets)
    return MappingResponse(mappings=suggested, unmapped_columns=unmapped)
@router.post("/validate", response_model=ValidationResponse)
async def validate_alias(file: UploadFile = File(...), category: str | None = Form(None), reader: TabularUploadReader = Depends(get_upload_reader), quality: QualityService = Depends(get_quality_service)) -> ValidationResponse:
    return await _validate_upload(file, category, reader, quality)
@router.post("/validations", response_model=ValidationResponse)
async def validate(file: UploadFile = File(...), category: str | None = Form(None), reader: TabularUploadReader = Depends(get_upload_reader), quality: QualityService = Depends(get_quality_service)) -> ValidationResponse:
    return await _validate_upload(file, category, reader, quality)

async def _read_frame(
    file: UploadFile,
    reader: TabularUploadReader,
):
    try:
        return reader.read(file.filename, await file.read())
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


async def _validate_upload(
    file: UploadFile,
    category: str | None,
    reader: TabularUploadReader,
    service: QualityService,
) -> ValidationResponse:
    content = await file.read()
    try:
        logger.info("validation_requested", extra={"event": "validation_requested", "upload_filename": file.filename, "requested_category": category})
        frame = reader.read(file.filename, content)
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

