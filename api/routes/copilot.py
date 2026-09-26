"""Copilot API routes."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from agents.planner import PlannerAgent
from agents.requirement import RequirementAgent
from api.dependencies import get_copilot_service, get_current_user
from application.copilot.contracts import CopilotAction, CopilotApprovalEvent
from application.copilot.service import CopilotService
from domain.identity import CurrentUser
from schemas.copilot import (
    CopilotAuthorWorkflowRequest,
    CopilotAuthorWorkflowResponse,
    CopilotChatRequest,
    CopilotSessionResponse,
    CopilotPlanStepResponse,
    CopilotWorkflowPlanResponse,
)


router = APIRouter(tags=["Copilot"])


def _author_workflow_response(result) -> CopilotAuthorWorkflowResponse:
    action = next(
        (
            item
            for item in result.actions
            if item.action == "workflow_plan"
        ),
        None,
    )

    if action is None:
        raise HTTPException(
            status_code=500,
            detail="Copilot returned no workflow plan",
        )

    requirement = action.arguments["requirement"]
    plan = action.arguments["plan"]

    return CopilotAuthorWorkflowResponse(
        message=result.message,
        project_id=action.arguments["project_id"],
        name=action.arguments["name"],
        requested_category=requirement.requested_category,
        requested_capabilities=list(requirement.requested_capabilities),
        requested_intents=list(requirement.requested_intents),
        parameters=requirement.parameters,
        plan=CopilotWorkflowPlanResponse(
            version=plan.version,
            steps=[
                CopilotPlanStepResponse(
                    capability_id=step.capability_id,
                    capability_version=step.capability_version,
                    parameters=dict(step.parameters),
                    input_mapping=dict(step.input_mapping),
                )
                for step in plan.steps
            ],
            metadata=dict(plan.metadata),
        ),
    )


@router.post(
    "/copilot/sessions",
    response_model=CopilotSessionResponse,
     summary='Create Copilot session',
     description='Create a Copilot session for the current user and return its session details.'
 )
def create_session(
    current_user: CurrentUser = Depends(get_current_user),
    copilot: CopilotService = Depends(get_copilot_service),
) -> CopilotSessionResponse:
    session = copilot.create_session(current_user=current_user)
    return CopilotSessionResponse(session_id=session.session_id)


@router.post(
    "/copilot/chat",
     summary='Stream Copilot chat',
     description='Send a message to the Copilot session and stream generated events, actions, and responses.'
 )
def chat(
    payload: CopilotChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    copilot: CopilotService = Depends(get_copilot_service),
) -> StreamingResponse:
    def event_stream():
        for chunk in copilot.stream(
            current_user=current_user,
            user_message=payload.message,
            session_id=payload.session_id,
        ):
            if isinstance(chunk, CopilotAction):
                event = {
                    "type": "action",
                    "action": chunk.action,
                    "arguments": chunk.arguments,
                }
            elif isinstance(chunk, CopilotApprovalEvent):
                event = {
                    "type": "approval",
                    "approval": chunk.approval,
                }
            else:
                event = {
                    "type": "text",
                    "content": chunk,
                }

            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
    )

@router.post(
    "/copilot/author-workflow",
    response_model=CopilotAuthorWorkflowResponse,
     summary='Author workflow with Copilot',
     description='Use Copilot workflow-authoring input to create or propose a workflow and return the authoring result.'
 )
def author_workflow(
    payload: CopilotAuthorWorkflowRequest,
    current_user: CurrentUser = Depends(get_current_user),
    copilot: CopilotService = Depends(get_copilot_service),
) -> CopilotAuthorWorkflowResponse:
    try:
        result = copilot.author_workflow(
            current_user=current_user,
            project_id=payload.project_id,
            name=payload.name,
            user_request=payload.user_request,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return _author_workflow_response(result)
