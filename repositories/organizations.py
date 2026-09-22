"""Repository for organization persistence."""

from __future__ import annotations

from typing import Callable
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import OrganizationRecord


class OrganizationRepository:
    def __init__(
        self,
        sessions: Callable[[], Session],
    ) -> None:
        self._sessions = sessions

    def create(
        self,
        *,
        organization_id: str | None = None,
        name: str,
    ) -> OrganizationRecord:
        with self._sessions() as session:
            record = OrganizationRecord(
                id=organization_id or str(uuid4()),
                name=name,
            )

            session.add(record)
            session.commit()
            session.refresh(record)

            return record

    def get(
        self,
        organization_id: str,
    ) -> OrganizationRecord | None:
        with self._sessions() as session:
            return session.get(
                OrganizationRecord,
                organization_id,
            )

    def list(self) -> list[OrganizationRecord]:
        with self._sessions() as session:
            return list(
                session.scalars(
                    select(OrganizationRecord).order_by(
                        OrganizationRecord.created_at
                    )
                )
            )
