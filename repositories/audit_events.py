"""Repository for immutable, workspace-scoped audit events."""
from __future__ import annotations
from datetime import timezone

from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import (
    AuditEventRecord,
    WorkspaceRecord,
)
from domain.audit import AuditEvent


class AuditEventRepository:
    def __init__(
        self,
        sessions: Callable[[], Session],
    ) -> None:
        self._sessions = sessions

    @staticmethod
    def _to_domain(
        record: AuditEventRecord,
    ) -> AuditEvent:
        return AuditEvent(
            id=record.id,
            workspace_id=record.workspace_id,
            actor_id=record.actor_id,
            action=record.action,
            resource_type=record.resource_type,
            resource_id=record.resource_id,
            execution_id=record.execution_id,
            changeset_id=record.changeset_id,
            metadata=record.metadata_json or {},
            created_at=(
                record.created_at.replace(tzinfo=timezone.utc)
                if record.created_at.tzinfo is None
                else record.created_at.astimezone(timezone.utc)
            ),
            previous_hash=record.previous_hash,
            event_hash=record.event_hash,
        )

    def add(
        self,
        event: AuditEvent,
    ) -> AuditEvent:
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
        event: AuditEvent,
    ) -> AuditEventRecord:
        if not event.event_hash:
            raise ValueError(
                "AuditEvent must have an event_hash before persistence"
            )

        record = AuditEventRecord(
            id=event.id,
            workspace_id=event.workspace_id,
            actor_id=event.actor_id,
            action=event.action,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            execution_id=event.execution_id,
            changeset_id=event.changeset_id,
            metadata_json=event.metadata,
            created_at=event.created_at,
            previous_hash=event.previous_hash,
            event_hash=event.event_hash,
        )

        session.add(record)
        session.flush()
        return record

    def lock_workspace(
        self,
        session: Session,
        workspace_id: str,
    ) -> WorkspaceRecord:
        workspace = session.scalar(
            select(WorkspaceRecord)
            .where(WorkspaceRecord.id == workspace_id)
            .with_for_update()
        )

        if workspace is None:
            raise ValueError(
                f"Workspace not found: {workspace_id}"
            )

        return workspace

    def get_latest_in_transaction(
        self,
        session: Session,
        workspace_id: str,
    ) -> AuditEventRecord | None:
        return session.scalar(
            select(AuditEventRecord)
            .where(
                AuditEventRecord.workspace_id == workspace_id
            )
            .order_by(
                AuditEventRecord.created_at.desc(),
                AuditEventRecord.id.desc(),
            )
            .limit(1)
        )

    def list_for_owner(
        self,
        *,
        owner_id: str,
        workspace_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        execution_id: str | None = None,
        changeset_id: str | None = None,
    ) -> list[AuditEvent]:
        with self._sessions() as session:
            query = (
                select(AuditEventRecord)
                .join(
                    WorkspaceRecord,
                    AuditEventRecord.workspace_id
                    == WorkspaceRecord.id,
                )
                .where(
                    WorkspaceRecord.owner_id == owner_id
                )
            )

            if workspace_id is not None:
                query = query.where(
                    AuditEventRecord.workspace_id == workspace_id
                )

            if resource_type is not None:
                query = query.where(
                    AuditEventRecord.resource_type == resource_type
                )

            if resource_id is not None:
                query = query.where(
                    AuditEventRecord.resource_id == resource_id
                )

            if execution_id is not None:
                query = query.where(
                    AuditEventRecord.execution_id == execution_id
                )

            if changeset_id is not None:
                query = query.where(
                    AuditEventRecord.changeset_id == changeset_id
                )

            query = query.order_by(
                AuditEventRecord.created_at.asc(),
                AuditEventRecord.id.asc(),
            )

            records = list(session.scalars(query))

            return [
                self._to_domain(record)
                for record in records
            ]



