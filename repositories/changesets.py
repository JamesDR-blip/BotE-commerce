"""Repository for immutable ChangeSet persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from database.models import (
    ChangeSetItemRecord,
    ChangeSetRecord,
    DatasetRecord,
    ProjectRecord,
    WorkspaceRecord,
)
from domain.changeset import (
    ChangeSet,
    ChangeSetItem,
    ChangeSetStatus,
)


class ChangeSetRepository:

    def __init__(
        self,
        sessions: Callable[[], Session],
    ) -> None:
        self._sessions = sessions

    def create(
        self,
        changeset: ChangeSet,
        items: list[ChangeSetItem],
    ) -> ChangeSet:
        with self._sessions() as session:
            record = self._add(
                session,
                changeset,
                items,
            )
            session.commit()
            session.refresh(record)
            return self._to_domain(record)

    def get(
        self,
        changeset_id: str,
    ) -> ChangeSet | None:
        with self._sessions() as session:
            record = session.get(
                ChangeSetRecord,
                changeset_id,
            )

            if record is None:
                return None

            return self._to_domain(record)

    def get_for_owner(
        self,
        *,
        changeset_id: str,
        owner_id: str,
    ) -> ChangeSet | None:
        with self._sessions() as session:
            record = session.scalar(
                select(ChangeSetRecord)
                .join(
                    DatasetRecord,
                    ChangeSetRecord.dataset_id == DatasetRecord.id,
                )
                .join(
                    ProjectRecord,
                    DatasetRecord.project_id == ProjectRecord.id,
                )
                .join(
                    WorkspaceRecord,
                    ProjectRecord.workspace_id == WorkspaceRecord.id,
                )
                .where(
                    ChangeSetRecord.id == changeset_id,
                    WorkspaceRecord.owner_id == owner_id,
                )
            )

            if record is None:
                return None

            return self._to_domain(record)

    def list_for_owner(
        self,
        *,
        owner_id: str,
    ) -> list[ChangeSet]:
        with self._sessions() as session:
            records = list(
                session.scalars(
                    select(ChangeSetRecord)
                    .join(
                        DatasetRecord,
                        ChangeSetRecord.dataset_id == DatasetRecord.id,
                    )
                    .join(
                        ProjectRecord,
                        DatasetRecord.project_id == ProjectRecord.id,
                    )
                    .join(
                        WorkspaceRecord,
                        ProjectRecord.workspace_id == WorkspaceRecord.id,
                    )
                    .where(
                        WorkspaceRecord.owner_id == owner_id,
                    )
                    .order_by(
                        ChangeSetRecord.created_at.desc()
                    )
                )
            )

            return [
                self._to_domain(record)
                for record in records
            ]

    def list_items_for_owner(
        self,
        *,
        changeset_id: str,
        owner_id: str,
    ) -> list[ChangeSetItem] | None:
        with self._sessions() as session:
            changeset_exists = session.scalar(
                select(ChangeSetRecord.id)
                .join(
                    DatasetRecord,
                    ChangeSetRecord.dataset_id == DatasetRecord.id,
                )
                .join(
                    ProjectRecord,
                    DatasetRecord.project_id == ProjectRecord.id,
                )
                .join(
                    WorkspaceRecord,
                    ProjectRecord.workspace_id == WorkspaceRecord.id,
                )
                .where(
                    ChangeSetRecord.id == changeset_id,
                    WorkspaceRecord.owner_id == owner_id,
                )
            )

            if changeset_exists is None:
                return None

            records = list(
                session.scalars(
                    select(ChangeSetItemRecord)
                    .where(
                        ChangeSetItemRecord.changeset_id
                        == changeset_id
                    )
                    .order_by(
                        ChangeSetItemRecord.record_id
                    )
                )
            )

            return [
                ChangeSetItem(
                    id=record.id,
                    changeset_id=record.changeset_id,
                    entity=record.entity,
                    record_id=record.record_id,
                    before_snapshot=record.before_snapshot,
                    after_snapshot=record.after_snapshot,
                )
                for record in records
            ]

    def list_by_dataset(
        self,
        dataset_id: str,
    ) -> list[ChangeSet]:
        with self._sessions() as session:
            records = list(
                session.scalars(
                    select(ChangeSetRecord)
                    .where(
                        ChangeSetRecord.dataset_id == dataset_id
                    )
                    .order_by(
                        ChangeSetRecord.created_at
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
    ) -> list[ChangeSet]:
        with self._sessions() as session:
            records = list(
                session.scalars(
                    select(ChangeSetRecord)
                    .where(
                        ChangeSetRecord.execution_id == execution_id
                    )
                    .order_by(
                        ChangeSetRecord.created_at
                    )
                )
            )

            return [
                self._to_domain(record)
                for record in records
            ]

    def add_in_transaction(
        self,
        session: Session,
        changeset: ChangeSet,
        items: list[ChangeSetItem],
    ) -> ChangeSetRecord:
        return self._add(
            session,
            changeset,
            items,
        )

    def get_record_in_transaction(
        self,
        session: Session,
        changeset_id: str,
    ) -> ChangeSetRecord | None:
        return session.get(
            ChangeSetRecord,
            changeset_id,
        )

    def apply_in_transaction(
        self,
        session: Session,
        *,
        changeset_id: str,
        expected_before_storage_key: str,
        applied_at: datetime | None = None,
    ) -> ChangeSetRecord:
        changeset = session.get(
            ChangeSetRecord,
            changeset_id,
        )

        if changeset is None:
            raise ValueError(
                f"ChangeSet not found: {changeset_id}"
            )

        if changeset.status != ChangeSetStatus.PREPARED.value:
            raise ValueError(
                "Only PREPARED ChangeSets can be applied: "
                f"{changeset_id} ({changeset.status})"
            )

        result = session.execute(
            update(DatasetRecord)
            .where(
                DatasetRecord.id == changeset.dataset_id,
                DatasetRecord.storage_key
                == expected_before_storage_key,
            )
            .values(
                storage_key=changeset.after_storage_key,
                content_hash=changeset.after_content_hash,
            )
        )

        if result.rowcount != 1:
            raise ValueError(
                "Dataset storage pointer changed before ChangeSet "
                f"could be applied: {changeset.dataset_id}"
            )

        changeset.status = ChangeSetStatus.APPLIED.value
        changeset.applied_at = (
            applied_at or datetime.now(timezone.utc)
        )

        session.flush()
        return changeset

    def rollback_in_transaction(
        self,
        session: Session,
        *,
        changeset_id: str,
        expected_after_storage_key: str,
        rolled_back_at: datetime | None = None,
    ) -> ChangeSetRecord:
        changeset = session.get(
            ChangeSetRecord,
            changeset_id,
        )

        if changeset is None:
            raise ValueError(
                f"ChangeSet not found: {changeset_id}"
            )

        if changeset.status != ChangeSetStatus.APPLIED.value:
            raise ValueError(
                "Only APPLIED ChangeSets can be rolled back: "
                f"{changeset_id} ({changeset.status})"
            )

        result = session.execute(
            update(DatasetRecord)
            .where(
                DatasetRecord.id == changeset.dataset_id,
                DatasetRecord.storage_key
                == expected_after_storage_key,
            )
            .values(
                storage_key=changeset.before_storage_key,
                content_hash=changeset.before_content_hash,
            )
        )

        if result.rowcount != 1:
            raise ValueError(
                "Dataset storage pointer changed before ChangeSet "
                f"could be rolled back: {changeset.dataset_id}"
            )

        changeset.status = ChangeSetStatus.ROLLED_BACK.value
        changeset.rolled_back_at = (
            rolled_back_at or datetime.now(timezone.utc)
        )

        session.flush()
        return changeset

    def _add(
        self,
        session: Session,
        changeset: ChangeSet,
        items: list[ChangeSetItem],
    ) -> ChangeSetRecord:
        record = ChangeSetRecord(
            id=changeset.id,
            dataset_id=changeset.dataset_id,
            execution_id=changeset.execution_id,
            workflow_id=changeset.workflow_id,
            workflow_version=changeset.workflow_version,
            before_storage_key=changeset.before_storage_key,
            before_content_hash=changeset.before_content_hash,
            after_storage_key=changeset.after_storage_key,
            after_content_hash=changeset.after_content_hash,
            status=changeset.status.value,
            created_at=changeset.created_at,
            applied_at=changeset.applied_at,
            rolled_back_at=changeset.rolled_back_at,
        )

        session.add(record)

        session.add_all(
            [
                ChangeSetItemRecord(
                    id=item.id,
                    changeset_id=item.changeset_id,
                    entity=item.entity,
                    record_id=item.record_id,
                    before_snapshot=item.before_snapshot,
                    after_snapshot=item.after_snapshot,
                )
                for item in items
            ]
        )

        return record

    def to_domain(
        self,
        record: ChangeSetRecord,
    ) -> ChangeSet:
        return self._to_domain(record)

    def _to_domain(
        self,
        record: ChangeSetRecord,
    ) -> ChangeSet:
        return ChangeSet(
            id=record.id,
            dataset_id=record.dataset_id,
            execution_id=record.execution_id,
            workflow_id=record.workflow_id,
            workflow_version=record.workflow_version,
            before_storage_key=record.before_storage_key,
            before_content_hash=record.before_content_hash,
            after_storage_key=record.after_storage_key,
            after_content_hash=record.after_content_hash,
            status=ChangeSetStatus(record.status),
            created_at=record.created_at,
            applied_at=record.applied_at,
            rolled_back_at=record.rolled_back_at,
        )
