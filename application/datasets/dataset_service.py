"""Application service for dataset management."""

from __future__ import annotations

from typing import Any

from repositories.datasets import DatasetRepository
from repositories.projects import ProjectRepository
from application.datasets.dataset_ingestion import DatasetIngestionService
from domain.identity import CurrentUser

class DatasetService:
    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        projects: ProjectRepository,
        ingestion: DatasetIngestionService | None = None,
    ) -> None:
        self.datasets = datasets
        self.projects = projects
        self.ingestion = ingestion

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

        if self.projects.get_for_owner(
            project_id=project_id,
            owner_id=current_user.user_id,
        ) is None:
            raise ValueError(
                f"Project not found: {project_id}"
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
        if self.projects.get_for_owner(
            project_id=project_id,
            owner_id=current_user.user_id,
        ) is None:
            raise ValueError(
                f"Project not found: {project_id}"
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
        if self.projects.get_for_owner(
            project_id=project_id,
            owner_id=current_user.user_id,
        ) is None:
            raise ValueError(
                f"Project not found: {project_id}"
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
        return self.datasets.get_for_owner(
            dataset_id=dataset_id,
            owner_id=current_user.user_id,
        )

    def list_datasets(
        self,
        *,
        current_user: CurrentUser,
        project_id: str,
    ):
        return self.datasets.list_by_project_for_owner(
            project_id=project_id,
            owner_id=current_user.user_id,
        )
