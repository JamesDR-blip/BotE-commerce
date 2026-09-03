"""AI Studio API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import (
    get_current_user,
    get_studio_service,
)
from domain.identity import CurrentUser
from schemas.requests import (
    ProjectCreateRequest,
    WorkspaceCreateRequest,
)
from schemas.responses import (
    ProjectResponse,
    WorkspaceResponse,
)
from services.studio_service import StudioService

router = APIRouter()

@router.post(
    "/workspaces",
    response_model=WorkspaceResponse,
)
def create_workspace(
    payload: WorkspaceCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    studio: StudioService = Depends(get_studio_service),
) -> WorkspaceResponse:
    workspace = studio.create_workspace(
        workspace_id=payload.id,
        name=payload.name,
    )

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        created_at=workspace.created_at,
    )


@router.get(
    "/workspaces/{workspace_id}",
    response_model=WorkspaceResponse,
)
def get_workspace(
    workspace_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    studio: StudioService = Depends(get_studio_service),
) -> WorkspaceResponse:
    workspace = studio.get_workspace(workspace_id)

    if workspace is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workspace not found: {workspace_id}",
        )

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        created_at=workspace.created_at,
    )

@router.post(
    "/projects",
    response_model=ProjectResponse,
)
def create_project(
    payload: ProjectCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    studio: StudioService = Depends(get_studio_service),
) -> ProjectResponse:
    project = studio.create_project(
        project_id=payload.id,
        workspace_id=payload.workspace_id,
        name=payload.name,
        description=payload.description,
    )

    return ProjectResponse(
        id=project.id,
        workspace_id=project.workspace_id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
    )


@router.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    studio: StudioService = Depends(get_studio_service),
) -> ProjectResponse:
    project = studio.get_project(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project not found: {project_id}",
        )

    return ProjectResponse(
        id=project.id,
        workspace_id=project.workspace_id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
    )


@router.get(
    "/workspaces/{workspace_id}/projects",
    response_model=list[ProjectResponse],
)
def list_projects(
    workspace_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    studio: StudioService = Depends(get_studio_service),
) -> list[ProjectResponse]:
    projects = studio.list_projects(workspace_id)

    return [
        ProjectResponse(
            id=project.id,
            workspace_id=project.workspace_id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
        )
        for project in projects
    ]