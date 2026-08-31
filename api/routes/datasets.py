"""Dataset API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from api.dependencies import get_studio_service
from services.studio_service import StudioService
from schemas.requests import DatasetCreateRequest
from schemas.responses import DatasetResponse


router = APIRouter()


def _dataset_response(dataset) -> DatasetResponse:
    metadata = getattr(dataset, "metadata_json", None)

    if metadata is None:
        metadata = getattr(dataset, "metadata", {})

    return DatasetResponse(
        id=dataset.id,
        project_id=dataset.project_id,
        name=dataset.name,
        source_type=dataset.source_type,
        filename=dataset.filename,
        file_format=dataset.file_format,
        size_bytes=dataset.size_bytes,
        content_hash=dataset.content_hash,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        status=dataset.status,
        metadata=metadata,
        created_at=dataset.created_at,
    )


@router.post(
    "/datasets",
    response_model=DatasetResponse,
)
def create_dataset(
    payload: DatasetCreateRequest,
    studio: StudioService = Depends(get_studio_service),
) -> DatasetResponse:
    dataset = studio.create_dataset(
        dataset_id=payload.id,
        project_id=payload.project_id,
        name=payload.name,
        source_type=payload.source_type,
        metadata=payload.metadata,
    )

    return _dataset_response(dataset)


@router.post(
    "/projects/{project_id}/datasets/upload",
    response_model=DatasetResponse,
)
async def upload_dataset(
    project_id: str,
    name: str = Form(...),
    file: UploadFile = File(...),
    studio: StudioService = Depends(get_studio_service),
) -> DatasetResponse:
    content = await file.read()

    try:
        dataset = studio.ingest_dataset(
            dataset_id=f"dataset-{uuid.uuid4().hex}",
            project_id=project_id,
            name=name,
            filename=file.filename or "",
            content=content,
            source_type="upload",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return _dataset_response(dataset)


@router.get(
    "/datasets/{dataset_id}",
    response_model=DatasetResponse,
)
def get_dataset(
    dataset_id: str,
    studio: StudioService = Depends(get_studio_service),
) -> DatasetResponse:
    dataset = studio.get_dataset(dataset_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset not found: {dataset_id}",
        )

    return _dataset_response(dataset)


@router.get(
    "/projects/{project_id}/datasets",
    response_model=list[DatasetResponse],
)
def list_datasets(
    project_id: str,
    studio: StudioService = Depends(get_studio_service),
) -> list[DatasetResponse]:
    datasets = studio.list_datasets(project_id)

    return [
        _dataset_response(dataset)
        for dataset in datasets
    ]