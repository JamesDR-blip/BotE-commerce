"""Application service for workflow authoring."""

from __future__ import annotations

import json

from domain.identity import CurrentUser
from domain.plans import ExecutionPlan
from repositories.projects import ProjectRepository
from repositories.workflows import WorkflowRepository
from services.execution_plan_serializer import ExecutionPlanSerializer

class WorkflowAuthoringService:
    def __init__(
        self,
        *,
        workflows: WorkflowRepository,
        projects: ProjectRepository,
    ) -> None:
        self.workflows = workflows
        self.projects = projects

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
            raise ValueError(
                f"Project not found: {project_id}"
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
        return self.workflows.get_for_owner(
            workflow_id=workflow_id,
            owner_id=current_user.user_id,
        )

    def list_workflows(
        self,
        *,
        current_user: CurrentUser,
        project_id: str,
    ):
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
            raise ValueError(
                f"Workflow not found: {workflow_id}"
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
            raise ValueError(
                f"Workflow not found: {workflow_id}"
            )

        return self.workflows.activate_version(
            workflow_id,
            version,
        )