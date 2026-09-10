"""Application service for tenant-scoped agent memory."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from domain.agent_memory import AgentMemory, CorrectionEvent, ExecutionLearning
from repositories.agent_memory import AgentMemoryRepository

from application.memory.redaction import redact_memory_value


class AgentMemoryService:
    """Record and query agent memory without exposing persistence to agents."""

    def __init__(
        self,
        *,
        memories: AgentMemoryRepository,
    ) -> None:
        self._memories = memories

    def record_correction(
        self,
        event: CorrectionEvent,
        *,
        expires_at: datetime | None = None,
        memory_id: str | None = None,
    ) -> AgentMemory:
        value = {
            "previous_value": redact_memory_value(event.previous_value),
            "corrected_value": redact_memory_value(event.corrected_value),
            "context": redact_memory_value(event.context),
        }

        memory = AgentMemory(
            memory_id=memory_id or str(uuid4()),
            workspace_id=event.workspace_id,
            user_id=event.user_id,
            memory_type="correction",
            key=event.key,
            value=value,
            created_at=datetime.now().astimezone(),
            expires_at=expires_at,
        )

        return self._memories.create(memory)

    def record_learning(
        self,
        learning: ExecutionLearning,
        *,
        expires_at: datetime | None = None,
        memory_id: str | None = None,
    ) -> AgentMemory:
        value = {
            "execution_id": learning.execution_id,
            "value": redact_memory_value(learning.value),
            "context": redact_memory_value(learning.context),
        }

        memory = AgentMemory(
            memory_id=memory_id or str(uuid4()),
            workspace_id=learning.workspace_id,
            user_id=learning.user_id,
            memory_type="execution_learning",
            key=learning.key,
            value=value,
            created_at=datetime.now().astimezone(),
            expires_at=expires_at,
        )

        return self._memories.create(memory)

    def query(
        self,
        *,
        workspace_id: str,
        user_id: str,
        memory_type: str | None = None,
        key: str | None = None,
        now: datetime | None = None,
    ) -> list[AgentMemory]:
        return self._memories.list_for_scope(
            workspace_id=workspace_id,
            user_id=user_id,
            memory_type=memory_type,
            key=key,
            now=now,
        )

    def evict_expired(self, *, now: datetime | None = None) -> int:
        return self._memories.evict_expired(now=now)


__all__ = ["AgentMemoryService"]
