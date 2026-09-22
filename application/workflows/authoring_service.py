"""Application service for workflow authoring."""

from __future__ import annotations

import json

from domain.identity import CurrentUser
from domain.plans import ExecutionPlan
from repositories.projects import ProjectRepository
from repositories.workflows import WorkflowRepository
from repositories.workspaces import WorkspaceRepository
from services.authorization import AuthorizationService

from domain.serialization.execution_plan import ExecutionPlanSerializer


class WorkflowAuthoringService:
    def __init__(
        self,
        *,
        workflows: WorkflowRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository | None = None,
        authorization: AuthorizationService | None = None,
    ) -> None:
        self.workflows = workflows
        self.projects = projects
        self.workspaces = workspaces
        self.authorization = authorization

    def _organization_id_for_project(
        self,
        *,
        project_id: str,
        owner_id: str,
    ) -> str | None:
        if self.authorization is None:
            return None

        if self.workspaces is None:
            raise RuntimeError(
                "Workspace repository is required for workflow authorization"
            )

        project = self.projects.get_for_owner(
            project_id=project_id,
            owner_id=owner_id,
        )
        if project is None:
            raise ValueError(f"Project not found: {project_id}")

        workspace = self.workspaces.get_for_owner(
            workspace_id=project.workspace_id,
            owner_id=owner_id,
        )
        if workspace is None:
            raise ValueError(f"Workspace not found: {project.workspace_id}")

        return workspace.organization_id

    def _organization_id_for_workflow(
        self,
        *,
        workflow_id: str,
        owner_id: str,
    ) -> str | None:
        workflow = self.workflows.get_for_owner(
            workflow_id=workflow_id,
            owner_id=owner_id,
        )
        if workflow is None:
            return None

        return self._organization_id_for_project(
            project_id=workflow.project_id,
            owner_id=owner_id,
        )

    def _authorize(
        self,
        *,
        current_user: CurrentUser,
        action: str,
        organization_id: str | None,
    ) -> None:
        if self.authorization is None or organization_id is None:
            return

        self.authorization.authorize(
            user=current_user,
            resource="workflow",
            action=action,
            organization_id=organization_id,
        )

    def save_workflow(
        self,
        *,
        current_user: CurrentUser,
        workflow_id: str,
        project_id: str,
        name: str,
        version: str,
        plan: ExecutionPlan,
    ):
        project = self.projects.get_for_owner(
            project_id=project_id,
            owner_id=current_user.user_id,
        )
        if project is None:
            raise ValueError(f"Project not found: {project_id}")

        organization_id = self._organization_id_for_project(
            project_id=project_id,
            owner_id=current_user.user_id,
        )
        self._authorize(
            current_user=current_user,
            action="write",
            organization_id=organization_id,
        )

        plan_json = ExecutionPlanSerializer.to_dict(plan)

        return self.workflows.create(
            workflow_id=workflow_id,
            project_id=project_id,
            name=name,
            version=version,
            plan_json=json.dumps(
                plan_json,
                default=str,
            ),
        )

    def get_workflow(
        self,
        *,
        current_user: CurrentUser,
        workflow_id: str,
    ):
        workflow = self.workflows.get_for_owner(
            workflow_id=workflow_id,
            owner_id=current_user.user_id,
        )
        if workflow is None:
            return None

        organization_id = self._organization_id_for_workflow(
            workflow_id=workflow_id,
            owner_id=current_user.user_id,
        )
        self._authorize(
            current_user=current_user,
            action="read",
            organization_id=organization_id,
        )

        return workflow

    def list_workflows(
        self,
        *,
        current_user: CurrentUser,
        project_id: str,
    ):
        project = self.projects.get_for_owner(
            project_id=project_id,
            owner_id=current_user.user_id,
        )
        if project is None:
            return []

        organization_id = self._organization_id_for_project(
            project_id=project_id,
            owner_id=current_user.user_id,
        )
        self._authorize(
            current_user=current_user,
            action="read",
            organization_id=organization_id,
        )

        return self.workflows.list_by_project_for_owner(
            project_id=project_id,
            owner_id=current_user.user_id,
        )

    def create_workflow_version(
        self,
        *,
        current_user: CurrentUser,
        workflow_id: str,
        version: str,
        plan: ExecutionPlan,
    ):
        workflow = self.workflows.get_for_owner(
            workflow_id=workflow_id,
            owner_id=current_user.user_id,
        )
        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")

        organization_id = self._organization_id_for_workflow(
            workflow_id=workflow_id,
            owner_id=current_user.user_id,
        )
        self._authorize(
            current_user=current_user,
            action="write",
            organization_id=organization_id,
        )

        plan_json = ExecutionPlanSerializer.to_dict(plan)

        return self.workflows.create_version(
            workflow_id=workflow_id,
            version=version,
            plan_json=json.dumps(
                plan_json,
                default=str,
            ),
        )

    def get_workflow_version(
        self,
        *,
        current_user: CurrentUser,
        workflow_id: str,
        version: str,
    ):
        workflow = self.workflows.get_for_owner(
            workflow_id=workflow_id,
            owner_id=current_user.user_id,
        )
        if workflow is None:
            return None

        organization_id = self._organization_id_for_workflow(
            workflow_id=workflow_id,
            owner_id=current_user.user_id,
        )
        self._authorize(
            current_user=current_user,
            action="read",
            organization_id=organization_id,
        )

        return self.workflows.get_version_for_owner(
            workflow_id=workflow_id,
            version=version,
            owner_id=current_user.user_id,
        )

    def list_workflow_versions(
        self,
        *,
        current_user: CurrentUser,
        workflow_id: str,
    ):
        workflow = self.workflows.get_for_owner(
            workflow_id=workflow_id,
            owner_id=current_user.user_id,
        )
        if workflow is None:
            return []

        organization_id = self._organization_id_for_workflow(
            workflow_id=workflow_id,
            owner_id=current_user.user_id,
        )
        self._authorize(
            current_user=current_user,
            action="read",
            organization_id=organization_id,
        )

        return self.workflows.list_versions_for_owner(
            workflow_id=workflow_id,
            owner_id=current_user.user_id,
        )

    def activate_workflow_version(
        self,
        *,
        current_user: CurrentUser,
        workflow_id: str,
        version: str,
    ):
        workflow = self.workflows.get_for_owner(
            workflow_id=workflow_id,
            owner_id=current_user.user_id,
        )
        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")

        organization_id = self._organization_id_for_workflow(
            workflow_id=workflow_id,
            owner_id=current_user.user_id,
        )
        self._authorize(
            current_user=current_user,
            action="write",
            organization_id=organization_id,
        )

        return self.workflows.activate_version(
            workflow_id=workflow_id,
            version=version,
        )
