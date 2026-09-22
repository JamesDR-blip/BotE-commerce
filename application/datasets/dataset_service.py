"""Application service for dataset management."""

from __future__ import annotations

from typing import Any

from repositories.datasets import DatasetRepository
from repositories.projects import ProjectRepository
from repositories.workspaces import WorkspaceRepository
from application.datasets.dataset_ingestion import DatasetIngestionService
from domain.identity import CurrentUser
from services.authorization import AuthorizationService

class DatasetService:
    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository | None = None,
        ingestion: DatasetIngestionService | None = None,
        authorization: AuthorizationService | None = None,
    ) -> None:
        self.datasets = datasets
        self.projects = projects
        self.workspaces = workspaces
        self.ingestion = ingestion
        self.authorization = authorization

    def _authorize(
        self,
        *,
        current_user: CurrentUser,
        action: str,
        organization_id: str | None,
    ) -> None:
        if self.authorization is None:
            return

        # Legacy resources created before S24 may not belong to an
        # organization. Their existing owner/project scope remains
        # authoritative until they are assigned to a tenant.
        if organization_id is None:
            return

        self.authorization.authorize(
            user=current_user,
            resource="dataset",
            action=action,
            organization_id=organization_id,
        )

    def _organization_id_for_project(
        self,
        *,
        project_id: str,
        owner_id: str,
    ) -> str | None:
        # Legacy/unit-test construction may omit authorization and the
        # workspace repository. In that mode preserve the pre-S24 behavior.
        if self.authorization is None:
            return None

        if self.workspaces is None:
            raise RuntimeError(
                "Workspace repository is required for authorized dataset operations"
            )

        workspace = self.workspaces.get_for_owner(
            workspace_id=self.projects.get_for_owner(
                project_id=project_id,
                owner_id=owner_id,
            ).workspace_id,
            owner_id=owner_id,
        )

        if workspace is None:
            raise ValueError(
                f"Workspace not found for project: {project_id}"
            )

        return workspace.organization_id

    def create_dataset(
        self,
        *,
        dataset_id: str,
        project_id: str,
        name: str,
        current_user: CurrentUser,
        source_type: str,
        metadata: dict[str, Any],
    ):
        project = self.projects.get_for_owner(
            project_id=project_id,
            owner_id=current_user.user_id,
        )

        if project is None:
            raise ValueError(
                f"Project not found: {project_id}"
            )

        self._authorize(
            current_user=current_user,
            action="write",
            organization_id=self._organization_id_for_project(
                project_id=project_id,
                owner_id=current_user.user_id,
            ),
        )

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
        current_user: CurrentUser,
        filename: str,
        content: bytes,
        source_type: str = "upload",
    ):
        project = self.projects.get_for_owner(
            project_id=project_id,
            owner_id=current_user.user_id,
        )

        if project is None:
            raise ValueError(
                f"Project not found: {project_id}"
            )

        self._authorize(
            current_user=current_user,
            action="write",
            organization_id=self._organization_id_for_project(
                project_id=project_id,
                owner_id=current_user.user_id,
            ),
        )

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

    def ingest_dataset_stream(
        self,
        *,
        dataset_id: str,
        project_id: str,
        name: str,
        current_user: CurrentUser,
        filename: str,
        source,
        source_type: str = "upload",
    ):
        project = self.projects.get_for_owner(
            project_id=project_id,
            owner_id=current_user.user_id,
        )

        if project is None:
            raise ValueError(
                f"Project not found: {project_id}"
            )

        self._authorize(
            current_user=current_user,
            action="write",
            organization_id=self._organization_id_for_project(
                project_id=project_id,
                owner_id=current_user.user_id,
            ),
        )

        if self.ingestion is None:
            raise RuntimeError(
                "Dataset ingestion service is not configured"
            )

        return self.ingestion.ingest_streaming(
            dataset_id=dataset_id,
            project_id=project_id,
            name=name,
            filename=filename,
            source=source,
            source_type=source_type,
        )

    def get_dataset(
        self,
        *,
        current_user: CurrentUser,
        dataset_id: str,
    ):
        dataset = self.datasets.get_for_owner(
            dataset_id=dataset_id,
            owner_id=current_user.user_id,
        )

        if dataset is None:
            return None

        project = self.projects.get_for_owner(
            project_id=dataset.project_id,
            owner_id=current_user.user_id,
        )

        if project is None:
            return None

        self._authorize(
            current_user=current_user,
            action="read",
            organization_id=self._organization_id_for_project(
                project_id=dataset.project_id,
                owner_id=current_user.user_id,
            ),
        )

        return dataset

    def list_datasets(
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

        self._authorize(
            current_user=current_user,
            action="read",
            organization_id=self._organization_id_for_project(
                project_id=project_id,
                owner_id=current_user.user_id,
            ),
        )

        return self.datasets.list_by_project_for_owner(
            project_id=project_id,
            owner_id=current_user.user_id,
        )
