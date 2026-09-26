"""ChangeSet API routes."""

from __future__ import annotations

import inspect

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import (
    get_changeset_query_service,
    get_changeset_rollback_service,
    get_current_user,
)
from application.changesets.query_service import ChangeSetQueryService
from application.changesets.rollback_service import ChangeSetRollbackService
from domain.identity import CurrentUser
from schemas.responses import (
    ChangeSetDetailResponse,
    ChangeSetItemResponse,
    ChangeSetResponse,
    ChangeSetRollbackResponse,
)

router = APIRouter(tags=["ChangeSets"])


def _changeset_response(changeset) -> ChangeSetResponse:
    return ChangeSetResponse(
        id=changeset.id,
        dataset_id=changeset.dataset_id,
        execution_id=changeset.execution_id,
        workflow_id=changeset.workflow_id,
        workflow_version=changeset.workflow_version,
        before_content_hash=changeset.before_content_hash,
        after_content_hash=changeset.after_content_hash,
        status=changeset.status.value,
        created_at=changeset.created_at,
        applied_at=changeset.applied_at,
        rolled_back_at=changeset.rolled_back_at,
    )


@router.get(
    "/changesets",
    response_model=list[ChangeSetResponse],
     summary='List change sets',
     description='Return change sets visible to the current user, optionally filtered by the supported query parameters.'
 )
def list_changesets(
    current_user: CurrentUser = Depends(get_current_user),
    query_service: ChangeSetQueryService = Depends(
        get_changeset_query_service
    ),
):
    return [
        _changeset_response(changeset)
        for changeset in query_service.list_changesets(
            current_user=current_user,
        )
    ]


@router.get(
    "/changesets/{changeset_id}",
    response_model=ChangeSetDetailResponse,
     summary='Get change set',
     description='Return the details of a specific change set.'
 )
def get_changeset(
    changeset_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    query_service: ChangeSetQueryService = Depends(
        get_changeset_query_service
    ),
):
    changeset = query_service.get_changeset(
        current_user=current_user,
        changeset_id=changeset_id,
    )

    if changeset is None:
        raise HTTPException(
            status_code=404,
            detail=f"ChangeSet not found: {changeset_id}",
        )

    items = query_service.get_items(
        current_user=current_user,
        changeset_id=changeset_id,
    )

    if items is None:
        raise HTTPException(
            status_code=404,
            detail=f"ChangeSet not found: {changeset_id}",
        )

    return ChangeSetDetailResponse(
        **_changeset_response(changeset).model_dump(),
        items=[
            ChangeSetItemResponse(
                id=item.id,
                changeset_id=item.changeset_id,
                entity=item.entity,
                record_id=item.record_id,
                before_snapshot=item.before_snapshot,
                after_snapshot=item.after_snapshot,
            )
            for item in items
        ],
    )


@router.post(
    "/changesets/{changeset_id}/rollback",
    response_model=ChangeSetRollbackResponse,
     summary='Rollback change set',
     description='Request rollback of a change set and return the resulting rollback record.'
 )
def rollback_changeset(
    changeset_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    query_service: ChangeSetQueryService = Depends(
        get_changeset_query_service
    ),
    rollback_service: ChangeSetRollbackService = Depends(
        get_changeset_rollback_service
    ),
):
    changeset = query_service.get_changeset(
        current_user=current_user,
        changeset_id=changeset_id,
    )

    if changeset is None:
        raise HTTPException(
            status_code=404,
            detail=f"ChangeSet not found: {changeset_id}",
        )

    try:
        rollback_method = rollback_service.rollback
        rollback_parameters = inspect.signature(
            rollback_method
        ).parameters

        if "actor_id" in rollback_parameters:
            rolled_back = rollback_method(
                changeset_id=changeset_id,
                actor_id=current_user.user_id,
            )
        else:
            rolled_back = rollback_method(
                changeset_id=changeset_id,
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return ChangeSetRollbackResponse(
        status="rollback_completed",
        changeset=_changeset_response(rolled_back),
    )
