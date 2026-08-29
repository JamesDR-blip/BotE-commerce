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
