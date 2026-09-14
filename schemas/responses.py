"""HTTP response contracts."""
from typing import Any
from datetime import datetime

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
    filename: str | None = None
    file_format: str | None = None
    size_bytes: int | None = None
    content_hash: str | None = None
    row_count: int | None = None
    column_count: int | None = None
    status: str
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


class WorkflowExecutionResponse(BaseModel):
    execution_id: str
    workflow_id: str
    workflow_version: str
    status: str
    success: bool
    outputs: dict[str, Any]
    error: str | None = None
    changeset_id: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class SimulationRowDiffResponse(BaseModel):
    row_index: int
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None


class SimulationTabularDiffResponse(BaseModel):
    input_key: str
    before_rows: int
    after_rows: int
    before_columns: list[str]
    after_columns: list[str]
    added_rows: int
    removed_rows: int
    changed_rows: int
    row_diffs: list[SimulationRowDiffResponse]
    truncated: bool


class SimulationDiffResponse(BaseModel):
    tabular: list[SimulationTabularDiffResponse]
    changed_keys: list[str]


class WorkflowSimulationResponse(BaseModel):
    simulation_id: str
    workflow_id: str
    workflow_version: str
    success: bool
    outputs: dict[str, Any]
    diff: SimulationDiffResponse
    error: str | None = None


class WorkflowExecutionStatusResponse(BaseModel):
    execution_id: str
    workflow_id: str
    workflow_version: str
    status: str
    success: bool
    error: str | None = None
    started_at: datetime | None = None
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


class RuleSearchRequestEcho(BaseModel):
    query: str
    category: str | None = None
    fields: list[str]
    top_k: int


class RetrievedRuleMatchResponse(BaseModel):
    rule_id: str
    content: str
    score: float
    category: str | None = None
    metadata: dict[str, Any]


class RuleSearchResponse(BaseModel):
    query: RuleSearchRequestEcho
    matches: list[RetrievedRuleMatchResponse]


class HealthMetricResponse(BaseModel):
    dimension: str
    score: float
    assessed: bool


class DatasetHealthResponse(BaseModel):
    dataset_id: str
    dataset_name: str
    aggregate: float
    metrics: list[HealthMetricResponse]


class HealthMetricsResponse(BaseModel):
    project_id: str
    items: list[DatasetHealthResponse]


class IssueDiagnosticResponse(BaseModel):
    code: str
    field: str
    message: str
    severity: str
    count: int


class RemediationProposalResponse(BaseModel):
    id: str
    diagnostic_code: str
    action: str
    rationale: str
    severity: str
    status: str


class DiagnosticsResponse(BaseModel):
    dataset_id: str
    diagnostics: list[IssueDiagnosticResponse]
    remediation_proposals: list[RemediationProposalResponse]


"""API response schemas for ChangeSets."""

class ChangeSetResponse(BaseModel):
    id: str
    dataset_id: str
    execution_id: str
    workflow_id: str
    workflow_version: str
    before_content_hash: str
    after_content_hash: str
    status: str
    created_at: datetime
    applied_at: datetime | None = None
    rolled_back_at: datetime | None = None


class ChangeSetItemResponse(BaseModel):
    id: str
    changeset_id: str
    entity: str
    record_id: str
    before_snapshot: dict[str, Any]
    after_snapshot: dict[str, Any]


class ChangeSetDetailResponse(ChangeSetResponse):
    items: list[ChangeSetItemResponse]


class ChangeSetRollbackResponse(BaseModel):
    status: str
    changeset: ChangeSetResponse


class LineageEventResponse(BaseModel):
    id: str
    dataset_id: str
    execution_id: str
    workflow_id: str
    workflow_version: str
    capability_id: str
    capability_version: str
    event_type: str
    input_refs: dict[str, Any]
    output_refs: dict[str, Any]
    created_at: datetime | None = None


class AuditEventResponse(BaseModel):
    id: str
    workspace_id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    execution_id: str | None = None
    changeset_id: str | None = None
    metadata: dict[str, Any]
    created_at: datetime | None = None
    previous_hash: str | None = None
    event_hash: str | None = None
