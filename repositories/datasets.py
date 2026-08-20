"""Repository for dataset persistence."""

from __future__ import annotations

from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import DatasetRecord


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
    ) -> DatasetRecord:

        with self._sessions() as session:

            record = DatasetRecord(
                id=dataset_id,
                project_id=project_id,
                name=name,
                source_type=source_type,
                metadata_json=metadata,
            )

            session.add(record)
            session.commit()
            session.refresh(record)

            return record


    def get(
        self,
        dataset_id: str,
    ) -> DatasetRecord | None:

        with self._sessions() as session:
            return session.get(
                DatasetRecord,
                dataset_id,
            )


    def list_by_project(
        self,
        project_id: str,
    ) -> list[DatasetRecord]:

        with self._sessions() as session:

            return list(
                session.scalars(
                    select(DatasetRecord)
                    .where(
                        DatasetRecord.project_id
                        == project_id
                    )
                )
            )