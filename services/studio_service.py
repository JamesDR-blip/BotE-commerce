"""Application service for AI Studio resources."""

from __future__ import annotations

import json
from typing import Any

from domain.plans import ExecutionPlan

from repositories.workspaces import WorkspaceRepository
from repositories.projects import ProjectRepository
from repositories.datasets import DatasetRepository
from repositories.workflows import WorkflowRepository

from services.execution_plan_serializer import ExecutionPlanSerializer


class StudioService:
    """
    Application facade for AI Studio entities.

    Responsible for coordinating:
    Workspace
    Project
    Dataset
    Workflow
    """

    def __init__(
        self,
        *,
        workspaces: WorkspaceRepository,
        projects: ProjectRepository,
        datasets: DatasetRepository,
        workflows: WorkflowRepository,
    ) -> None:

        self.workspaces = workspaces
        self.projects = projects
        self.datasets = datasets
        self.workflows = workflows


    # -------------------------
    # Workspace
    # -------------------------

    def create_workspace(
        self,
        *,
        workspace_id: str,
        name: str,
    ):

        return self.workspaces.create(
            workspace_id=workspace_id,
            name=name,
        )


    def get_workspace(
        self,
        workspace_id: str,
    ):

        return self.workspaces.get(
            workspace_id
        )


    # -------------------------
    # Project
    # -------------------------

    def create_project(
        self,
        *,
        project_id: str,
        workspace_id: str,
        name: str,
        description: str | None = None,
    ):

        return self.projects.create(
            project_id=project_id,
            workspace_id=workspace_id,
            name=name,
            description=description,
        )


    def list_projects(
        self,
        workspace_id: str,
    ):

        return self.projects.list_by_workspace(
            workspace_id
        )


    # -------------------------
    # Dataset
    # -------------------------

    def create_dataset(
        self,
        *,
        dataset_id: str,
        project_id: str,
        name: str,
        source_type: str,
        metadata: dict[str, Any],
    ):

        return self.datasets.create(
            dataset_id=dataset_id,
            project_id=project_id,
            name=name,
            source_type=source_type,
            metadata=metadata,
        )


    def list_datasets(
        self,
        project_id: str,
    ):

        return self.datasets.list_by_project(
            project_id
        )


    # -------------------------
    # Workflow
    # -------------------------

    def save_workflow(
        self,
        *,
        workflow_id: str,
        project_id: str,
        name: str,
        version: str,
        plan: ExecutionPlan,
    ):

        plan_json = (
            ExecutionPlanSerializer
            .to_dict(plan)
        )

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