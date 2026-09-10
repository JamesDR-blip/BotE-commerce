from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping


@dataclass(frozen=True)
class AgentMemory:
    """Tenant-scoped memory available to an AI agent."""

    memory_id: str
    workspace_id: str
    user_id: str
    memory_type: str
    key: str
    value: Mapping[str, object]
    created_at: datetime
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.memory_id.strip():
            raise ValueError("Memory id cannot be empty")
        if not self.workspace_id.strip():
            raise ValueError("Workspace id cannot be empty")
        if not self.user_id.strip():
            raise ValueError("User id cannot be empty")
        if not self.memory_type.strip():
            raise ValueError("Memory type cannot be empty")
        if not self.key.strip():
            raise ValueError("Memory key cannot be empty")

        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise ValueError("Memory expiry must be after creation")


@dataclass(frozen=True)
class CorrectionEvent:
    """User correction that can improve future agent decisions."""

    workspace_id: str
    user_id: str
    correction_type: str
    key: str
    previous_value: object | None = None
    corrected_value: object | None = None
    context: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.workspace_id.strip():
            raise ValueError("Workspace id cannot be empty")
        if not self.user_id.strip():
            raise ValueError("User id cannot be empty")
        if not self.correction_type.strip():
            raise ValueError("Correction type cannot be empty")
        if not self.key.strip():
            raise ValueError("Correction key cannot be empty")


@dataclass(frozen=True)
class ExecutionLearning:
    """Learning captured from a completed workflow execution."""

    workspace_id: str
    user_id: str
    execution_id: str
    key: str
    value: Mapping[str, object]
    context: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.workspace_id.strip():
            raise ValueError("Workspace id cannot be empty")
        if not self.user_id.strip():
            raise ValueError("User id cannot be empty")
        if not self.execution_id.strip():
            raise ValueError("Execution id cannot be empty")
        if not self.key.strip():
            raise ValueError("Learning key cannot be empty")
