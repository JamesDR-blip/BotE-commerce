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
from services.dataset_ingestion import DatasetIngestionService

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
        ingestion: DatasetIngestionService | None = None,
    ) -> None:

        self.workspaces = workspaces
        self.projects = projects
        self.datasets = datasets
        self.workflows = workflows
        self.ingestion = ingestion


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

    def get_project(
        self,
        project_id: str,
    ):
        return self.projects.get(project_id)


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

    def ingest_dataset(
        self,
        *,
        dataset_id: str,
        project_id: str,
        name: str,
        filename: str,
        content: bytes,
        source_type: str = "upload",
    ):
        if self.ingestion is None:
            raise RuntimeError(
                "Dataset ingestion service is not configured"
            )

        return self.ingestion.ingest(
            dataset_id=dataset_id,
            project_id=project_id,
            name=name,
            filename=filename,
            content=content,
            source_type=source_type,
        )        

    def get_dataset(
        self,
        dataset_id: str,
    ):
        return self.datasets.get(
            dataset_id
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
        plan_json = (
            ExecutionPlanSerializer
            .to_dict(plan)
        )

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
