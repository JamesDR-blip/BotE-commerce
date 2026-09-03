"""Application service for workflow authoring."""

from __future__ import annotations

import json

from domain.plans import ExecutionPlan
from repositories.workflows import WorkflowRepository
from services.execution_plan_serializer import ExecutionPlanSerializer


class WorkflowAuthoringService:
    def __init__(
        self,
        *,
        workflows: WorkflowRepository,
    ) -> None:
        self.workflows = workflows

    def save_workflow(
        self,
        *,
        workflow_id: str,
        project_id: str,
        name: str,
        version: str,
        plan: ExecutionPlan,
    ):
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
        workflow_id: str,
    ):
        return self.workflows.get(
            workflow_id
        )

    def list_workflows(
        self,
        project_id: str,
    ):
        return self.workflows.list_by_project(
            project_id
        )

    def create_workflow_version(
        self,
        *,
        workflow_id: str,
        version: str,
        plan: ExecutionPlan,
    ):
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
        workflow_id: str,
        version: str,
    ):
        return self.workflows.get_version(
            workflow_id,
            version,
        )

    def list_workflow_versions(
        self,
        workflow_id: str,
    ):
        return self.workflows.list_versions(
            workflow_id
        )

    def activate_workflow_version(
        self,
        workflow_id: str,
        version: str,
    ):
        return self.workflows.activate_version(
            workflow_id,
            version,
        )