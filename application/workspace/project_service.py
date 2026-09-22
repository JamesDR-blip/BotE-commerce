"""Application service for workspace and project ownership."""

from __future__ import annotations

from domain.identity import CurrentUser
from services.authorization import AuthorizationService
from repositories.projects import ProjectRepository
from repositories.workspaces import WorkspaceRepository


class WorkspaceProjectService:
    def __init__(
        self,
        *,
        workspaces: WorkspaceRepository,
        projects: ProjectRepository,
        authorization: AuthorizationService | None = None,
    ) -> None:
        self.workspaces = workspaces
        self.projects = projects
        self.authorization = authorization

    def _authorize(
        self,
        *,
        current_user: CurrentUser,
        resource: str,
        action: str,
        organization_id: str | None,
    ) -> None:
        if self.authorization is None:
            return

        if organization_id is None:
            return

        self.authorization.authorize(
            user=current_user,
            resource=resource,
            action=action,
            organization_id=organization_id,
        )

    def create_workspace(
        self,
        *,
        current_user: CurrentUser,
        workspace_id: str,
        name: str,
        organization_id: str | None = None,
    ):
        self._authorize(
            current_user=current_user,
            resource="workspace",
            action="manage",
            organization_id=organization_id,
        )

        return self.workspaces.create(
            workspace_id=workspace_id,
            owner_id=current_user.user_id,
            name=name,
            organization_id=organization_id,
        )

    def get_workspace(
        self,
        *,
        current_user: CurrentUser,
        workspace_id: str,
    ):
        workspace = self.workspaces.get_for_owner(
            workspace_id=workspace_id,
            owner_id=current_user.user_id,
        )

        if workspace is not None:
            self._authorize(
                current_user=current_user,
                resource="workspace",
                action="read",
                organization_id=workspace.organization_id,
            )

        return workspace

    def list_workspaces(
        self,
        *,
        current_user: CurrentUser,
    ):
        workspaces = self.workspaces.list_for_owner(
            current_user.user_id
        )

        for workspace in workspaces:
            self._authorize(
                current_user=current_user,
                resource="workspace",
                action="read",
                organization_id=workspace.organization_id,
            )

        return workspaces

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

        self._authorize(
            current_user=current_user,
            resource="workspace",
            action="manage",
            organization_id=workspace.organization_id,
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

        self._authorize(
            current_user=current_user,
            resource="workspace",
            action="read",
            organization_id=workspace.organization_id,
        )

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

        self._authorize(
            current_user=current_user,
            resource="workspace",
            action="read",
            organization_id=workspace.organization_id,
        )

        return self.projects.list_by_workspace(
            workspace_id
        )