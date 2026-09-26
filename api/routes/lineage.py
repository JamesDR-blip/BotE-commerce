"""Lineage and audit API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import (
    get_audit_service,
    get_current_user,
    get_dataset_service,
    get_lineage_tracking_service,
)
from application.audit.audit_service import AuditService
from application.datasets.dataset_service import DatasetService
from application.lineage.lineage_tracking_service import LineageTrackingService
from domain.identity import CurrentUser
from schemas.responses import AuditEventResponse, LineageEventResponse


router = APIRouter(tags=["Lineage"])


@router.get(
    "/datasets/{dataset_id}/lineage",
    response_model=list[LineageEventResponse],
     summary='Get dataset lineage',
     description='Return lineage events associated with the specified dataset.'
 )
def list_dataset_lineage(
    dataset_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    dataset_service: DatasetService = Depends(get_dataset_service),
    lineage_service: LineageTrackingService = Depends(
        get_lineage_tracking_service
    ),
) -> list[LineageEventResponse]:
    dataset = dataset_service.get_dataset(
        current_user=current_user,
        dataset_id=dataset_id,
    )

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset not found: {dataset_id}",
        )

    events = lineage_service.list_for_dataset(
        dataset_id=dataset_id,
        owner_id=current_user.user_id,
    )

    return [
        LineageEventResponse(
            id=event.id,
            dataset_id=event.dataset_id,
            execution_id=event.execution_id,
            workflow_id=event.workflow_id,
            workflow_version=event.workflow_version,
            capability_id=event.capability_id,
            capability_version=event.capability_version,
            event_type=event.event_type,
            input_refs=event.input_refs,
            output_refs=event.output_refs,
            created_at=event.created_at,
        )
        for event in events
    ]


@router.get(
    "/audit-logs",
    response_model=list[AuditEventResponse],
     summary='List audit logs',
     description='Return audit events for the current user, optionally filtered by workspace, resource, execution, or change set.'
 )
def list_audit_logs(
    current_user: CurrentUser = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service),
    workspace_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    execution_id: str | None = None,
    changeset_id: str | None = None,
) -> list[AuditEventResponse]:
    events = audit_service.list(
        owner_id=current_user.user_id,
        workspace_id=workspace_id,
        resource_type=resource_type,
        resource_id=resource_id,
        execution_id=execution_id,
        changeset_id=changeset_id,
    )

    return [
        AuditEventResponse(
            id=event.id,
            workspace_id=event.workspace_id,
            actor_id=event.actor_id,
            action=event.action,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            execution_id=event.execution_id,
            changeset_id=event.changeset_id,
            metadata=event.metadata,
            created_at=event.created_at,
            previous_hash=event.previous_hash,
            event_hash=event.event_hash,
        )
        for event in events
    ]
