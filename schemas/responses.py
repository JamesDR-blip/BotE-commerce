"""HTTP response contracts."""
from typing import Any

from pydantic import BaseModel

class ValidationResponse(BaseModel):
    execution_id: str
    category: str
    health_score: float
    reports: dict[str, str]
    cached: bool


class UploadResponse(BaseModel):
    filename: str
    rows: int
    columns: list[str]


class TabularPreviewResponse(BaseModel):
    category: str
    rows: int
    columns: list[str]
    records: list[dict[str, Any]]


class ExtractionRecordResponse(BaseModel):
    row: int
    attributes: dict[str, str]


class ExtractionResponse(BaseModel):
    records: list[ExtractionRecordResponse]


class MappingResponse(BaseModel):
    mappings: dict[str, str]
    unmapped_columns: list[str]


class ExecutionHistoryItem(BaseModel):
    id: str
    category: str
    health_score: float
    created_at: str


class HistoryResponse(BaseModel):
    items: list[ExecutionHistoryItem]
