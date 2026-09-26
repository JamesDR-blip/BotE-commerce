"""AI Studio API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import (
    get_current_user,
    get_workspace_project_service,
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
from application.workspace.project_service import WorkspaceProjectService

router = APIRouter(tags=["Studio"])

@router.post(
    "/workspaces",
    response_model=WorkspaceResponse,
     summary='Create workspace',
     description='Create a workspace for the current user.'
 )
def create_workspace(
    payload: WorkspaceCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    workspace_project_service: WorkspaceProjectService = Depends(get_workspace_project_service),
) -> WorkspaceResponse:
    workspace = workspace_project_service.create_workspace(
        current_user=current_user,
        workspace_id=payload.id,
        name=payload.name,
        organization_id=payload.organization_id,
    )

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        organization_id=workspace.organization_id,
        created_at=workspace.created_at,
    )


@router.get(
    "/workspaces/{workspace_id}",
    response_model=WorkspaceResponse,
     summary='Get workspace',
     description='Return a workspace visible to the current user.'
 )
def get_workspace(
    workspace_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    workspace_project_service: WorkspaceProjectService = Depends(get_workspace_project_service),
) -> WorkspaceResponse:
    workspace = workspace_project_service.get_workspace(
        current_user=current_user,
        workspace_id=workspace_id,
    )

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
     summary='Create project',
     description='Create a project in a workspace for the current user.'
 )
def create_project(
    payload: ProjectCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    workspace_project_service: WorkspaceProjectService = Depends(get_workspace_project_service),
) -> ProjectResponse:
    project = workspace_project_service.create_project(
        current_user=current_user,
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
     summary='Get project',
     description='Return a project visible to the current user.'
 )
def get_project(
    project_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    workspace_project_service: WorkspaceProjectService = Depends(get_workspace_project_service),
) -> ProjectResponse:
    project = workspace_project_service.get_project(
        current_user=current_user,
        project_id=project_id,
    )

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
     summary='List workspace projects',
     description='Return projects belonging to the requested workspace.'
 )
def list_projects(
    workspace_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    workspace_project_service: WorkspaceProjectService = Depends(get_workspace_project_service),
) -> list[ProjectResponse]:
    
    try:
        projects = workspace_project_service.list_projects(
            current_user=current_user,
            workspace_id=workspace_id,
        )
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Workspace not found: {workspace_id}",
        )

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
