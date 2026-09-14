"""Repository for immutable data lineage events."""
from __future__ import annotations

from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import (
    DataLineageEventRecord,
    DatasetRecord,
    ProjectRecord,
    WorkspaceRecord,
)
from domain.lineage import DataLineageEvent


class DataLineageEventRepository:
    def __init__(
        self,
        sessions: Callable[[], Session],
    ) -> None:
        self._sessions = sessions

    @staticmethod
    def _to_domain(
        record: DataLineageEventRecord,
    ) -> DataLineageEvent:
        return DataLineageEvent(
            id=record.id,
            dataset_id=record.dataset_id,
            execution_id=record.execution_id,
            workflow_id=record.workflow_id,
            workflow_version=record.workflow_version,
            capability_id=record.capability_id,
            capability_version=record.capability_version,
            event_type=record.event_type,
            input_refs=record.input_refs_json or {},
            output_refs=record.output_refs_json or {},
            created_at=record.created_at,
        )

    def add(
        self,
        event: DataLineageEvent,
    ) -> DataLineageEvent:
        with self._sessions() as session:
            record = self.add_in_transaction(
                session,
                event,
            )
            session.commit()
            session.refresh(record)
            return self._to_domain(record)

    def add_in_transaction(
        self,
        session: Session,
        event: DataLineageEvent,
    ) -> DataLineageEventRecord:
        record = DataLineageEventRecord(
            id=event.id,
            dataset_id=event.dataset_id,
            execution_id=event.execution_id,
            workflow_id=event.workflow_id,
            workflow_version=event.workflow_version,
            capability_id=event.capability_id,
            capability_version=event.capability_version,
            event_type=event.event_type,
            input_refs_json=event.input_refs,
            output_refs_json=event.output_refs,
            created_at=event.created_at,
        )
        session.add(record)
        session.flush()
        return record

    def list_for_dataset_owner(
        self,
        *,
        dataset_id: str,
        owner_id: str,
    ) -> list[DataLineageEvent]:
        with self._sessions() as session:
            records = list(
                session.scalars(
                    select(DataLineageEventRecord)
                    .join(
                        DatasetRecord,
                        DataLineageEventRecord.dataset_id
                        == DatasetRecord.id,
                    )
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
                        DataLineageEventRecord.dataset_id == dataset_id,
                        WorkspaceRecord.owner_id == owner_id,
                    )
                    .order_by(
                        DataLineageEventRecord.created_at.asc(),
                        DataLineageEventRecord.id.asc(),
                    )
                )
            )

            return [
                self._to_domain(record)
                for record in records
            ]

    def list_by_execution(
        self,
        execution_id: str,
    ) -> list[DataLineageEvent]:
        with self._sessions() as session:
            records = list(
                session.scalars(
                    select(DataLineageEventRecord)
                    .where(
                        DataLineageEventRecord.execution_id
                        == execution_id
                    )
                    .order_by(
                        DataLineageEventRecord.created_at.asc(),
                        DataLineageEventRecord.id.asc(),
                    )
                )
            )

            return [
                self._to_domain(record)
                for record in records
            ]


