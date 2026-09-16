from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import (
    get_channel_repository,
    get_channel_sync_service,
    get_current_user,
    get_sync_job_repository,
    get_workspace_project_service,
)
from application.channels.channel_sync_service import ChannelSyncService
from application.workspace.project_service import WorkspaceProjectService
from domain.channel_sync import Channel, SyncJob
from domain.identity import CurrentUser
from repositories.channels import ChannelRepository
from repositories.sync_jobs import SyncJobRepository
from schemas.requests import ChannelSyncRequest
from schemas.responses import ChannelResponse, SyncJobResponse


router = APIRouter()


def _channel_response(channel: Channel) -> ChannelResponse:
    return ChannelResponse(
        id=channel.id,
        workspace_id=channel.workspace_id,
        channel=channel.channel.value,
        name=channel.name,
        enabled=channel.enabled,
    )


def _sync_job_response(job: SyncJob) -> SyncJobResponse:
    return SyncJobResponse(
        id=job.id,
        workspace_id=job.workspace_id,
        dataset_id=job.dataset_id,
        channel_id=job.channel_id,
        idempotency_key=job.idempotency_key,
        status=job.status.value,
        error=job.error,
    )


@router.get(
    "/channels",
    response_model=list[ChannelResponse],
)
def list_channels(
    workspace_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    workspace_project_service: WorkspaceProjectService = Depends(
        get_workspace_project_service
    ),
    channel_repository: ChannelRepository = Depends(get_channel_repository),
) -> list[ChannelResponse]:
    workspace = workspace_project_service.get_workspace(
        current_user=current_user,
        workspace_id=workspace_id,
    )

    if workspace is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workspace not found: {workspace_id}",
        )

    channels = channel_repository.list_for_owner(
        workspace_id=workspace_id,
        owner_id=current_user.user_id,
    )

    return [_channel_response(channel) for channel in channels]


@router.post(
    "/channels/{channel_id}/sync",
    response_model=SyncJobResponse,
)
def sync_channel(
    channel_id: str,
    payload: ChannelSyncRequest,
    current_user: CurrentUser = Depends(get_current_user),
    channel_sync_service: ChannelSyncService = Depends(
        get_channel_sync_service
    ),
) -> SyncJobResponse:
    try:
        job = channel_sync_service.sync(
            current_user=current_user,
            channel_id=channel_id,
            dataset_id=payload.dataset_id,
            idempotency_key=payload.idempotency_key,
        )
    except ValueError as exc:
        detail = str(exc)

        if detail.startswith("Channel not found:"):
            status_code = 404
        elif detail.startswith("Dataset not found:"):
            status_code = 404
        elif detail.startswith("idempotency_key is already associated"):
            status_code = 409
        elif detail.startswith("Channel is disabled:"):
            status_code = 409
        else:
            status_code = 422

        raise HTTPException(
            status_code=status_code,
            detail=detail,
        ) from exc

    return _sync_job_response(job)


@router.get(
    "/sync-jobs/{sync_job_id}",
    response_model=SyncJobResponse,
)
def get_sync_job(
    sync_job_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    sync_job_repository: SyncJobRepository = Depends(
        get_sync_job_repository
    ),
) -> SyncJobResponse:
    job = sync_job_repository.get_for_owner(
        job_id=sync_job_id,
        owner_id=current_user.user_id,
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Sync job not found: {sync_job_id}",
        )

    return _sync_job_response(job)
