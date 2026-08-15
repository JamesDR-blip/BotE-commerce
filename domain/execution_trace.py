"""Execution trace domain contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CapabilityExecutionRecord:
    """Execution information for a single capability step."""

    capability_id: str
    capability_version: str
    status: str

    started_at: datetime
    finished_at: datetime | None = None

    duration_ms: float | None = None

    inputs: dict[str, Any] = field(
        default_factory=dict
    )

    outputs: dict[str, Any] = field(
        default_factory=dict
    )

    error: str | None = None


@dataclass(frozen=True)
class ExecutionTrace:
    """Complete trace of one execution plan run."""

    execution_id: str

    records: tuple[
        CapabilityExecutionRecord,
        ...
    ] = ()

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


__all__ = [
    "CapabilityExecutionRecord",
    "ExecutionTrace",
]