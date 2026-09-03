"""Application service for dataset management."""

from __future__ import annotations

from typing import Any

from repositories.datasets import DatasetRepository
from repositories.projects import ProjectRepository
from services.dataset_ingestion import DatasetIngestionService


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
        if self.projects.get(project_id) is None:
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

    def get_dataset(
        self,
        dataset_id: str,
    ):
        return self.datasets.get(dataset_id)

    def list_datasets(
        self,
        project_id: str,
    ):
        return self.datasets.list_by_project(
            project_id
        )