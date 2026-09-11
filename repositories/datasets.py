"""Repository for dataset persistence."""

from __future__ import annotations

from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import DatasetRecord, ProjectRecord, WorkspaceRecord
from domain.studio.dataset import Dataset


class DatasetRepository:

    def __init__(
        self,
        sessions: Callable[[], Session],
    ) -> None:
        self._sessions = sessions


    def create(
        self,
        *,
        dataset_id: str,
        project_id: str,
        name: str,
        source_type: str,
        metadata: dict[str, Any],
        filename: str | None = None,
        file_format: str | None = None,
        size_bytes: int | None = None,
        content_hash: str | None = None,
        storage_key: str | None = None,
        row_count: int | None = None,
        column_count: int | None = None,
        status: str = "READY",
    ) -> DatasetRecord:

        with self._sessions() as session:

            record = DatasetRecord(
                id=dataset_id,
                project_id=project_id,
                name=name,
                source_type=source_type,

                filename=filename,
                file_format=file_format,
                size_bytes=size_bytes,
                content_hash=content_hash,
                storage_key=storage_key,
                row_count=row_count,
                column_count=column_count,
                status=status,

                metadata_json=metadata,
            )

            session.add(record)
            session.commit()
            session.refresh(record)

            return record


    def _to_domain(self, record: DatasetRecord) -> Dataset:
        return Dataset(
            id=record.id,
            project_id=record.project_id,
            name=record.name,
            source_type=record.source_type,
            metadata=record.metadata_json or {},
            filename=record.filename,
            file_format=record.file_format,
            size_bytes=record.size_bytes,
            content_hash=record.content_hash,
            storage_key=record.storage_key,
            row_count=record.row_count,
            column_count=record.column_count,
            status=record.status,
            created_at=record.created_at,
        )

    def get(
        self,
        dataset_id: str,
    ) -> Dataset | None:

        with self._sessions() as session:
            record = session.get(
                DatasetRecord,
                dataset_id,
            )

            if record is None:
                return None

            return self._to_domain(record)

    def get_for_owner(
        self,
        *,
        dataset_id: str,
        owner_id: str,
    ) -> Dataset | None:

        with self._sessions() as session:
            record = session.scalar(
                select(DatasetRecord)
                .join(
                    ProjectRecord,
                    DatasetRecord.project_id
                    == ProjectRecord.id,
                )
                .join(
                    WorkspaceRecord,
                    ProjectRecord.workspace_id
                    == WorkspaceRecord.id,
                )
                .where(
                    DatasetRecord.id == dataset_id,
                    WorkspaceRecord.owner_id == owner_id,
                )
            )

            if record is None:
                return None

            return self._to_domain(record)


    def list_by_project(
        self,
        project_id: str,
    ) -> list[Dataset]:

        with self._sessions() as session:
            records = list(
                session.scalars(
                    select(DatasetRecord)
                    .where(
                        DatasetRecord.project_id == project_id
                    )
                )
            )

            return [
                self._to_domain(record)
                for record in records
            ]

    def list_by_project_for_owner(
        self,
        *,
        project_id: str,
        owner_id: str,
    ) -> list[Dataset]:

        with self._sessions() as session:
            records = list(
                session.scalars(
                    select(DatasetRecord)
                    .join(
                        ProjectRecord,
                        DatasetRecord.project_id
                        == ProjectRecord.id,
                    )
                    .join(
                        WorkspaceRecord,
                        ProjectRecord.workspace_id
                        == WorkspaceRecord.id,
                    )
                    .where(
                        DatasetRecord.project_id == project_id,
                        WorkspaceRecord.owner_id == owner_id,
                    )
                )
            )

            return [
                self._to_domain(record)
                for record in records
            ]