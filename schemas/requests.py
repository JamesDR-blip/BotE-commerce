from typing import Any

from pydantic import BaseModel, Field


class WorkspaceCreateRequest(BaseModel):
    id: str
    name: str


class ProjectCreateRequest(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: str | None = None


class DatasetCreateRequest(BaseModel):
    id: str
    project_id: str
    name: str
    source_type: str
    metadata: dict[str, Any]


class WorkflowCreateRequest(BaseModel):
    id: str
    project_id: str
    name: str
    version: str
    plan: dict[str, Any]


class WorkflowVersionCreateRequest(BaseModel):
    version: str
    plan: dict[str, Any]


class WorkflowExecutionRequest(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)
    dataset_id: str | None = None


class RuleSearchRequest(BaseModel):
    query: str
    category: str | None = None
    fields: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=50)


class RuleRecommendRequest(BaseModel):
    query: str
    category: str | None = None
    fields: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=50)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)


class ChannelSyncRequest(BaseModel):
    dataset_id: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
