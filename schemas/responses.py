"""HTTP response contracts."""
from typing import Any

from pydantic import BaseModel
from datetime import datetime

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

class CapabilityTraceResponse(BaseModel):
    capability_id: str
    capability_version: str
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ExecutionDetailResponse(BaseModel):
    execution_id: str
    category: str
    status: str
    health_score: float
    created_at: datetime
    requirement_json: str | None = None
    plan_json: str | None = None
    planner_version: str | None = None
    traces: list[CapabilityTraceResponse]


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    created_at: datetime

class ProjectResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: str | None = None
    created_at: datetime

class DatasetResponse(BaseModel):
    id: str
    project_id: str
    name: str
    source_type: str
    metadata: dict[str, Any]
    created_at: datetime

class WorkflowResponse(BaseModel):
    id: str
    project_id: str
    name: str
    active_version: str
    status: str
    created_at: datetime


class WorkflowVersionResponse(BaseModel):
    id: str
    workflow_id: str
    version: str
    plan: dict[str, Any]
    created_at: datetime

class WorkflowExecutionRequest(BaseModel):
    inputs: dict[str, Any] = {}


class WorkflowExecutionResponse(BaseModel):
    execution_id: str
    workflow_id: str
    workflow_version: str
    status: str
    success: bool
    outputs: dict[str, Any]
    error: str | None = None
    started_at: datetime
    finished_at: datetime | None = None

class WorkflowExecutionDetailResponse(BaseModel):
    execution_id: str
    workflow_id: str
    workflow_version: str
    status: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    error: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    traces: list[CapabilityTraceResponse]