"""Persistence contracts used by the application memory use cases."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from domain.agent_memory import AgentMemory


class AgentMemoryPersistencePort(Protocol):
    """Operations required by :class:`AgentMemoryService`."""

    def create(self, memory: AgentMemory) -> AgentMemory: ...

    def list_for_scope(
        self,
        *,
        workspace_id: str,
        user_id: str,
        memory_type: str | None = None,
        key: str | None = None,
        now: datetime | None = None,
    ) -> list[AgentMemory]: ...

    def evict_expired(self, *, now: datetime | None = None) -> int: ...


__all__ = ["AgentMemoryPersistencePort"]
