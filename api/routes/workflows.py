"""Workflow API routes."""

from __future__ import annotations
import json

from api.dependencies import (
    get_current_user,
    get_workflow_history,
    get_workflow_runtime,
    get_workflow_authoring_service,
)

from domain.identity import CurrentUser

from fastapi import APIRouter, Depends, HTTPException

from schemas.requests import (
    WorkflowCreateRequest,
    WorkflowExecutionRequest,
    WorkflowVersionCreateRequest,
)
from schemas.responses import (
    CapabilityTraceResponse,
    WorkflowExecutionDetailResponse,
    WorkflowExecutionResponse,
    WorkflowExecutionStatusResponse,
    WorkflowResponse,
    WorkflowVersionResponse,
)
from domain.serialization.execution_plan import ExecutionPlanSerializer
from application.workflows.authoring_service import WorkflowAuthoringService
from application.workflows.history_service import WorkflowHistoryService
from application.workflows.runtime_service import WorkflowRuntimeService


router = APIRouter()


def _execution_plan_from_payload(payload: dict):
    try:
        return ExecutionPlanSerializer.from_dict(payload)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid execution plan: {exc}",
        ) from exc


@router.post(
    "/workflows",
    response_model=WorkflowResponse,
)
def create_workflow(
    payload: WorkflowCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    authoring_service: WorkflowAuthoringService = Depends(
        get_workflow_authoring_service
    ),
) -> WorkflowResponse:
    plan = _execution_plan_from_payload(payload.plan)

    try:
        workflow = authoring_service.save_workflow(
            current_user=current_user,
            workflow_id=payload.id,
            project_id=payload.project_id,
            name=payload.name,
            version=payload.version,
            plan=plan,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return WorkflowResponse(
        id=workflow.id,
        project_id=workflow.project_id,
        name=workflow.name,
        active_version=workflow.active_version,
        status=workflow.status,
        created_at=workflow.created_at,
    )


@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowResponse,
)
def get_workflow(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    authoring_service: WorkflowAuthoringService = Depends(
        get_workflow_authoring_service
    ),
) -> WorkflowResponse:
    workflow = authoring_service.get_workflow(
        current_user=current_user,
        workflow_id=workflow_id,
    )

    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow not found: {workflow_id}",
        )

    return WorkflowResponse(
        id=workflow.id,
        project_id=workflow.project_id,
        name=workflow.name,
        active_version=workflow.active_version,
        status=workflow.status,
        created_at=workflow.created_at,
    )


@router.get(
    "/projects/{project_id}/workflows",
    response_model=list[WorkflowResponse],
)
def list_workflows(
    project_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    authoring_service: WorkflowAuthoringService = Depends(
        get_workflow_authoring_service
    ),
) -> list[WorkflowResponse]:
    workflows = authoring_service.list_workflows(
        current_user=current_user,
        project_id=project_id,
    )

    return [
        WorkflowResponse(
            id=workflow.id,
            project_id=workflow.project_id,
            name=workflow.name,
            active_version=workflow.active_version,
            status=workflow.status,
            created_at=workflow.created_at,
        )
        for workflow in workflows
    ]


@router.post(
    "/workflows/{workflow_id}/versions",
    response_model=WorkflowVersionResponse,
)
def create_workflow_version(
    workflow_id: str,
    payload: WorkflowVersionCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    authoring_service: WorkflowAuthoringService = Depends(
        get_workflow_authoring_service
    ),
) -> WorkflowVersionResponse:
    plan = _execution_plan_from_payload(payload.plan)

    try:
        version = authoring_service.create_workflow_version(
            current_user=current_user,
            workflow_id=workflow_id,
            version=payload.version,
            plan=plan,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return WorkflowVersionResponse(
        id=version.id,
        workflow_id=version.workflow_id,
        version=version.version,
        plan=json.loads(version.plan_json),
        created_at=version.created_at,
    )


@router.get(
    "/workflows/{workflow_id}/versions",
    response_model=list[WorkflowVersionResponse],
)
def list_workflow_versions(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    authoring_service: WorkflowAuthoringService = Depends(
        get_workflow_authoring_service
    ),
) -> list[WorkflowVersionResponse]:
    versions = authoring_service.list_workflow_versions(
        current_user=current_user,
        workflow_id=workflow_id,
    )

    return [
        WorkflowVersionResponse(
            id=version.id,
            workflow_id=version.workflow_id,
            version=version.version,
            plan=json.loads(version.plan_json),
            created_at=version.created_at,
        )
        for version in versions
    ]


@router.get(
    "/workflows/{workflow_id}/versions/{version}",
    response_model=WorkflowVersionResponse,
)
def get_workflow_version(
    workflow_id: str,
    version: str,
    current_user: CurrentUser = Depends(get_current_user),
    authoring_service: WorkflowAuthoringService = Depends(
        get_workflow_authoring_service
    ),
) -> WorkflowVersionResponse:
    record = authoring_service.get_workflow_version(
        current_user=current_user,
        workflow_id=workflow_id,
        version=version,
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow version not found: {version}",
        )

    return WorkflowVersionResponse(
        id=record.id,
        workflow_id=record.workflow_id,
        version=record.version,
        plan=json.loads(record.plan_json),
        created_at=record.created_at,
    )


@router.post(
    "/workflows/{workflow_id}/versions/{version}/activate",
    response_model=WorkflowResponse,
)
def activate_workflow_version(
    workflow_id: str,
    version: str,
    current_user: CurrentUser = Depends(get_current_user),
    authoring_service: WorkflowAuthoringService = Depends(
        get_workflow_authoring_service
    ),
) -> WorkflowResponse:
    try:
        workflow = authoring_service.activate_workflow_version(
            current_user=current_user,
            workflow_id=workflow_id,
            version=version,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return WorkflowResponse(
        id=workflow.id,
        project_id=workflow.project_id,
        name=workflow.name,
        active_version=workflow.active_version,
        status=workflow.status,
        created_at=workflow.created_at,
    )


@router.post(
    "/workflows/{workflow_id}/execute",
    response_model=WorkflowExecutionResponse,
)
def execute_workflow(
    workflow_id: str,
    payload: WorkflowExecutionRequest,
    runtime_service: WorkflowRuntimeService = Depends(
        get_workflow_runtime
    ),
) -> WorkflowExecutionResponse:
    try:
        runtime = runtime_service.execute(
            workflow_id=workflow_id,
            inputs=payload.inputs,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return WorkflowExecutionResponse(
        execution_id=runtime.execution_id,
        workflow_id=runtime.workflow_id,
        workflow_version=runtime.workflow_version,
        status=runtime.status.value,
        success=runtime.success,
        outputs=runtime.outputs,
        error=runtime.error,
        started_at=runtime.started_at,
        finished_at=runtime.finished_at,
    )


@router.post(
    "/workflows/{workflow_id}/execute-async",
    response_model=WorkflowExecutionResponse,
)
def execute_workflow_async(
    workflow_id: str,
    payload: WorkflowExecutionRequest,
    runtime_service: WorkflowRuntimeService = Depends(
        get_workflow_runtime
    ),
) -> WorkflowExecutionResponse:
    try:
        runtime = runtime_service.execute_async(
            workflow_id=workflow_id,
            inputs=payload.inputs,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return WorkflowExecutionResponse(
        execution_id=runtime.execution_id,
        workflow_id=runtime.workflow_id,
        workflow_version=runtime.workflow_version,
        status=runtime.status.value,
        success=runtime.success,
        outputs=runtime.outputs,
        error=runtime.error,
        started_at=runtime.started_at,
        finished_at=runtime.finished_at,
    )


@router.get(
    "/workflow-executions/{execution_id}/status",
    response_model=WorkflowExecutionStatusResponse,
)
def workflow_execution_status(
    execution_id: str,
    history_service: WorkflowHistoryService = Depends(
        get_workflow_history
    ),
) -> WorkflowExecutionStatusResponse:
    try:
        data = history_service.get_workflow_execution_detail(
            execution_id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return WorkflowExecutionStatusResponse(
        execution_id=data["execution_id"],
        workflow_id=data["workflow_id"],
        workflow_version=data["workflow_version"],
        status=data["status"],
        success=data["status"] == "COMPLETED",
        error=data["error"],
        started_at=data["started_at"],
        finished_at=data["finished_at"],
    )


@router.get(
    "/workflow-executions/{execution_id}",
    response_model=WorkflowExecutionDetailResponse,
)
def workflow_execution_detail(
    execution_id: str,
    history_service: WorkflowHistoryService = Depends(
        get_workflow_history
    ),
) -> WorkflowExecutionDetailResponse:
    try:
        data = history_service.get_workflow_execution_detail(
            execution_id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return WorkflowExecutionDetailResponse(
        execution_id=data["execution_id"],
        workflow_id=data["workflow_id"],
        workflow_version=data["workflow_version"],
        status=data["status"],
        inputs=data["inputs"],
        outputs=data["outputs"],
        error=data["error"],
        created_at=data["created_at"],
        started_at=data["started_at"],
        finished_at=data["finished_at"],
        traces=[
            CapabilityTraceResponse(
                capability_id=trace.capability_id,
                capability_version=trace.capability_version,
                status=trace.status,
                started_at=trace.started_at,
                finished_at=trace.finished_at,
            )
            for trace in data["traces"]
        ],
    )





