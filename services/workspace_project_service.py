"""Application service for workspace and project ownership."""

from __future__ import annotations

from domain.identity import CurrentUser
from repositories.projects import ProjectRepository
from repositories.workspaces import WorkspaceRepository


class WorkspaceProjectService:
    def __init__(
        self,
        *,
        workspaces: WorkspaceRepository,
        projects: ProjectRepository,
    ) -> None:
        self.workspaces = workspaces
        self.projects = projects

    def create_workspace(
        self,
        *,
        current_user: CurrentUser,
        workspace_id: str,
        name: str,
    ):
        return self.workspaces.create(
            workspace_id=workspace_id,
            owner_id=current_user.user_id,
            name=name,
        )

    def get_workspace(
        self,
        *,
        current_user: CurrentUser,
        workspace_id: str,
    ):
        return self.workspaces.get_for_owner(
            workspace_id=workspace_id,
            owner_id=current_user.user_id,
        )

    def list_workspaces(
        self,
        *,
        current_user: CurrentUser,
    ):
        return self.workspaces.list_for_owner(
            current_user.user_id
        )

    def create_project(
        self,
        *,
        current_user: CurrentUser,
        project_id: str,
        workspace_id: str,
        name: str,
        description: str | None = None,
    ):
        workspace = self.workspaces.get_for_owner(
            workspace_id=workspace_id,
            owner_id=current_user.user_id,
        )

        if workspace is None:
            raise ValueError(
                f"Workspace not found: {workspace_id}"
            )

        return self.projects.create(
            project_id=project_id,
            workspace_id=workspace_id,
            name=name,
            description=description,
        )

    def get_project(
        self,
        *,
        current_user: CurrentUser,
        project_id: str,
    ):
        project = self.projects.get(project_id)

        if project is None:
            return None

        workspace = self.workspaces.get_for_owner(
            workspace_id=project.workspace_id,
            owner_id=current_user.user_id,
        )

        if workspace is None:
            return None

        return project

    def list_projects(
        self,
        *,
        current_user: CurrentUser,
        workspace_id: str,
    ):
        workspace = self.workspaces.get_for_owner(
            workspace_id=workspace_id,
            owner_id=current_user.user_id,
        )

        if workspace is None:
            raise ValueError(
                f"Workspace not found: {workspace_id}"
            )

        return self.projects.list_by_workspace(
            workspace_id
        )