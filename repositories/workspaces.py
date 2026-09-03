"""Repository for workspace persistence."""

from __future__ import annotations

from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import WorkspaceRecord


class WorkspaceRepository:
    def __init__(
        self,
        sessions: Callable[[], Session],
    ) -> None:
        self._sessions = sessions

    def create(
        self,
        *,
        workspace_id: str,
        owner_id: str,
        name: str,
    ) -> WorkspaceRecord:

        with self._sessions() as session:
            record = WorkspaceRecord(
                id=workspace_id,
                owner_id=owner_id,
                name=name,
            )

            session.add(record)
            session.commit()
            session.refresh(record)

            return record

    def get(
        self,
        workspace_id: str,
    ) -> WorkspaceRecord | None:

        with self._sessions() as session:
            return session.get(
                WorkspaceRecord,
                workspace_id,
            )

    def list(self) -> list[WorkspaceRecord]:

        with self._sessions() as session:
            return list(
                session.scalars(
                    select(WorkspaceRecord)
                )
            )

    def get_for_owner(
        self,
        *,
        workspace_id: str,
        owner_id: str,
    ) -> WorkspaceRecord | None:

        with self._sessions() as session:
            return session.scalar(
                select(WorkspaceRecord)
                .where(
                    WorkspaceRecord.id == workspace_id,
                    WorkspaceRecord.owner_id == owner_id,
                )
            )

    def list_for_owner(
        self,
        owner_id: str,
    ) -> list[WorkspaceRecord]:

        with self._sessions() as session:
            return list(
                session.scalars(
                    select(WorkspaceRecord)
                    .where(
                        WorkspaceRecord.owner_id == owner_id
                    )
                )
            )