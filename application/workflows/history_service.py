"""Service for workflow execution history."""

from __future__ import annotations

import json

from domain.identity import CurrentUser
from services.authorization import AuthorizationService


class WorkflowHistoryService:

    def __init__(
        self,
        *,
        executions,
        traces,
        workflows=None,
        projects=None,
        workspaces=None,
        authorization: AuthorizationService | None = None,
    ) -> None:

        self.executions = executions
        self.traces = traces
        self.workflows = workflows
        self.projects = projects
        self.workspaces = workspaces
        self.authorization = authorization

    def _organization_id_for_execution(
        self,
        *,
        execution,
        current_user: CurrentUser,
    ) -> str | None:
        if self.authorization is None:
            return None

        if (
            self.workflows is None
            or self.projects is None
            or self.workspaces is None
        ):
            raise ValueError(
                "Workflow authorization dependencies are not configured"
            )

        workflow = self.workflows.get_for_owner(
            workflow_id=execution.workflow_id,
            owner_id=current_user.user_id,
        )
        if workflow is None:
            raise ValueError(
                f"Workflow execution not found: {execution.id}"
            )

        project = self.projects.get_for_owner(
            project_id=workflow.project_id,
            owner_id=current_user.user_id,
        )
        if project is None:
            raise ValueError(
                f"Workflow execution not found: {execution.id}"
            )

        workspace = self.workspaces.get_for_owner(
            workspace_id=project.workspace_id,
            owner_id=current_user.user_id,
        )
        if workspace is None:
            raise ValueError(
                f"Workflow execution not found: {execution.id}"
            )

        return workspace.organization_id

    def _authorize_execution_read(
        self,
        *,
        execution,
        current_user: CurrentUser | None,
    ) -> None:
        if self.authorization is None or current_user is None:
            return

        organization_id = self._organization_id_for_execution(
            execution=execution,
            current_user=current_user,
        )

        if organization_id is None:
            return

        self.authorization.authorize(
            user=current_user,
            resource="workflow",
            action="read",
            organization_id=organization_id,
        )

    def get_workflow_execution_detail(
        self,
        execution_id: str,
        current_user: CurrentUser | None = None,
    ):
        execution = self.executions.get(
            execution_id
        )

        if execution is None:
            raise ValueError(
                f"Workflow execution not found: {execution_id}"
            )

        self._authorize_execution_read(
            execution=execution,
            current_user=current_user,
        )

        traces = self.traces.list_by_execution(
            execution_id
        )

        return {
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "workflow_version": execution.workflow_version,
            "status": execution.status,
            "inputs": (
                json.loads(execution.inputs_json)
                if execution.inputs_json
                else {}
            ),
            "outputs": (
                json.loads(execution.outputs_json)
                if execution.outputs_json
                else {}
            ),
            "error": execution.error,
            "created_at": execution.created_at,
            "started_at": execution.started_at,
            "finished_at": execution.finished_at,
            "traces": traces,
        }