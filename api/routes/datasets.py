"""Dataset API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from api.dependencies import (
    get_dataset_service, 
    get_current_user,
)
from application.datasets.dataset_service import DatasetService
from schemas.requests import DatasetCreateRequest
from schemas.responses import DatasetResponse
from domain.identity import CurrentUser


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
    dataset_service: DatasetService = Depends(get_dataset_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> DatasetResponse:
    dataset = dataset_service.create_dataset(
        current_user=current_user,
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
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> DatasetResponse:
    content = await file.read()

    try:
        dataset = dataset_service.ingest_dataset(
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
    dataset_service: DatasetService = Depends(get_dataset_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> DatasetResponse:
    
    dataset = dataset_service.get_dataset(
        current_user=current_user,
        dataset_id=dataset_id,
    )

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
    dataset_service: DatasetService = Depends(get_dataset_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[DatasetResponse]:
    datasets = dataset_service.list_datasets(
        current_user=current_user,
        project_id=project_id,
    )

    return [
        _dataset_response(dataset)
        for dataset in datasets
    ]
