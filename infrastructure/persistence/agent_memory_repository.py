"""SQLAlchemy persistence adapter for tenant-scoped agent memory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from application.memory.ports import AgentMemoryPersistencePort
from database.models import AgentMemoryRecord
from domain.agent_memory import AgentMemory


class AgentMemoryRepository(AgentMemoryPersistencePort):
    """Persist agent memory through the existing SQLAlchemy schema."""

    def __init__(self, sessions: Callable[[], Session]) -> None:
        self._sessions = sessions

    @staticmethod
    def _to_domain(record: AgentMemoryRecord) -> AgentMemory:
        return AgentMemory(
            memory_id=record.id,
            workspace_id=record.workspace_id,
            user_id=record.user_id,
            memory_type=record.memory_type,
            key=record.memory_key,
            value=json.loads(record.value_json),
            created_at=record.created_at,
            expires_at=record.expires_at,
        )

    def create(self, memory: AgentMemory) -> AgentMemory:
        with self._sessions() as session:
            record = AgentMemoryRecord(
                id=memory.memory_id,
                workspace_id=memory.workspace_id,
                user_id=memory.user_id,
                memory_type=memory.memory_type,
                memory_key=memory.key,
                value_json=json.dumps(
                    dict(memory.value),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                created_at=memory.created_at,
                expires_at=memory.expires_at,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._to_domain(record)

    def list_for_scope(
        self,
        *,
        workspace_id: str,
        user_id: str,
        memory_type: str | None = None,
        key: str | None = None,
        now: datetime | None = None,
    ) -> list[AgentMemory]:
        current_time = now or datetime.now(timezone.utc)

        with self._sessions() as session:
            statement = select(AgentMemoryRecord).where(
                AgentMemoryRecord.workspace_id == workspace_id,
                AgentMemoryRecord.user_id == user_id,
            )

            if memory_type is not None:
                statement = statement.where(
                    AgentMemoryRecord.memory_type == memory_type
                )

            if key is not None:
                statement = statement.where(
                    AgentMemoryRecord.memory_key == key
                )

            statement = statement.where(
                (AgentMemoryRecord.expires_at.is_(None))
                | (AgentMemoryRecord.expires_at > current_time)
            ).order_by(AgentMemoryRecord.created_at.desc())

            return [
                self._to_domain(record)
                for record in session.scalars(statement)
            ]

    def evict_expired(self, *, now: datetime | None = None) -> int:
        current_time = now or datetime.now(timezone.utc)

        with self._sessions() as session:
            result = session.execute(
                delete(AgentMemoryRecord).where(
                    AgentMemoryRecord.expires_at.is_not(None),
                    AgentMemoryRecord.expires_at <= current_time,
                )
            )
            session.commit()
            return int(result.rowcount or 0)


__all__ = ["AgentMemoryRepository"]
