"""HTTP contracts for the Copilot API."""

from typing import Any

from pydantic import BaseModel, Field


class CopilotSessionResponse(BaseModel):
    session_id: str


class CopilotChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = Field(default=None, min_length=1)

class CopilotAuthorWorkflowRequest(BaseModel):
    project_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    user_request: str = Field(min_length=1)


class CopilotPlanStepResponse(BaseModel):
    capability_id: str
    capability_version: str
    parameters: dict[str, Any]
    input_mapping: dict[str, str]


class CopilotWorkflowPlanResponse(BaseModel):
    version: str
    steps: list[CopilotPlanStepResponse]
    metadata: dict[str, Any]


class CopilotAuthorWorkflowResponse(BaseModel):
    message: str
    project_id: str
    name: str
    requested_category: str | None = None
    requested_capabilities: list[str]
    requested_intents: list[str]
    parameters: dict[str, dict[str, Any]] | None = None
    plan: CopilotWorkflowPlanResponse
