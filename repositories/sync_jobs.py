"""Repositories for channel synchronization jobs and attempts."""
from __future__ import annotations

from datetime import timezone
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import (
    SyncAttemptRecord,
    SyncJobRecord,
    WorkspaceRecord,
)
from domain.channel_sync import (
    SyncAttempt,
    SyncAttemptStatus,
    SyncJob,
    SyncJobStatus,
)


class SyncJobRepository:
    """Persist workspace-scoped channel synchronization jobs."""

    def __init__(
        self,
        sessions: Callable[[], Session],
    ) -> None:
        self._sessions = sessions

    @staticmethod
    def _to_domain(record: SyncJobRecord) -> SyncJob:
        return SyncJob(
            id=record.id,
            workspace_id=record.workspace_id,
            dataset_id=record.dataset_id,
            channel_id=record.channel_id,
            idempotency_key=record.idempotency_key,
            status=SyncJobStatus(record.status),
            error=record.error,
        )

    def create(
        self,
        *,
        job: SyncJob,
    ) -> SyncJob:
        with self._sessions() as session:
            record = SyncJobRecord(
                id=job.id,
                workspace_id=job.workspace_id,
                dataset_id=job.dataset_id,
                channel_id=job.channel_id,
                idempotency_key=job.idempotency_key,
                status=job.status.value,
                error=job.error,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._to_domain(record)

    def get(
        self,
        job_id: str,
    ) -> SyncJob | None:
        with self._sessions() as session:
            record = session.get(SyncJobRecord, job_id)
            if record is None:
                return None
            return self._to_domain(record)

    def get_for_owner(
        self,
        *,
        job_id: str,
        owner_id: str,
    ) -> SyncJob | None:
        with self._sessions() as session:
            record = session.scalar(
                select(SyncJobRecord)
                .join(
                    WorkspaceRecord,
                    SyncJobRecord.workspace_id == WorkspaceRecord.id,
                )
                .where(
                    SyncJobRecord.id == job_id,
                    WorkspaceRecord.owner_id == owner_id,
                )
            )
            if record is None:
                return None
            return self._to_domain(record)

    def get_by_idempotency_key_for_owner(
        self,
        *,
        workspace_id: str,
        owner_id: str,
        idempotency_key: str,
    ) -> SyncJob | None:
        with self._sessions() as session:
            record = session.scalar(
                select(SyncJobRecord)
                .join(
                    WorkspaceRecord,
                    SyncJobRecord.workspace_id == WorkspaceRecord.id,
                )
                .where(
                    SyncJobRecord.workspace_id == workspace_id,
                    WorkspaceRecord.owner_id == owner_id,
                    SyncJobRecord.idempotency_key == idempotency_key,
                )
            )
            if record is None:
                return None
            return self._to_domain(record)

    def update(
        self,
        *,
        job: SyncJob,
    ) -> SyncJob:
        with self._sessions() as session:
            record = session.get(SyncJobRecord, job.id)
            if record is None:
                raise ValueError(f"SyncJob not found: {job.id}")

            record.status = job.status.value
            record.error = job.error
            session.commit()
            session.refresh(record)
            return self._to_domain(record)


class SyncAttemptRepository:
    """Persist bounded connector attempts."""

    def __init__(
        self,
        sessions: Callable[[], Session],
    ) -> None:
        self._sessions = sessions

    @staticmethod
    def _to_domain(record: SyncAttemptRecord) -> SyncAttempt:
        return SyncAttempt(
            id=record.id,
            sync_job_id=record.sync_job_id,
            attempt_number=record.attempt_number,
            status=SyncAttemptStatus(record.status),
            request_hash=record.request_hash,
            external_product_id=record.external_product_id,
            error=record.error,
        )

    def create(
        self,
        *,
        attempt: SyncAttempt,
    ) -> SyncAttempt:
        with self._sessions() as session:
            record = SyncAttemptRecord(
                id=attempt.id,
                sync_job_id=attempt.sync_job_id,
                attempt_number=attempt.attempt_number,
                status=attempt.status.value,
                request_hash=attempt.request_hash,
                external_product_id=attempt.external_product_id,
                error=attempt.error,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._to_domain(record)

    def list_for_job(
        self,
        *,
        sync_job_id: str,
    ) -> list[SyncAttempt]:
        with self._sessions() as session:
            records = session.scalars(
                select(SyncAttemptRecord)
                .where(SyncAttemptRecord.sync_job_id == sync_job_id)
                .order_by(
                    SyncAttemptRecord.attempt_number.asc(),
                    SyncAttemptRecord.id.asc(),
                )
            )
            return [self._to_domain(record) for record in records]
