"""Execution trace domain contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from domain.execution_status import ExecutionStatus

@dataclass(frozen=True)
class CapabilityExecutionRecord:
    """Execution information for a single capability step."""

    capability_id: str
    capability_version: str
    status: ExecutionStatus

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


    def summary(self) -> dict[str, object]:

        completed = sum(
            1
            for record in self.records
            if record.status == ExecutionStatus.COMPLETED
        )

        failed = sum(
            1
            for record in self.records
            if record.status == ExecutionStatus.FAILED
        )

        running = sum(
            1
            for record in self.records
            if record.status == ExecutionStatus.RUNNING
        )

        duration_ms = sum(
            record.duration_ms or 0
            for record in self.records
        )

        return {
            "execution_id": self.execution_id,
            "total_steps": len(self.records),
            "completed": completed,
            "failed": failed,
            "running": running,
            "duration_ms": duration_ms,
        }


__all__ = [
    "CapabilityExecutionRecord",
    "ExecutionTrace",
]