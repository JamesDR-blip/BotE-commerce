"""Execution trace collection service."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any, Mapping

from domain.execution_trace import (
    CapabilityExecutionRecord,
    ExecutionTrace,
)
from domain.execution_status import ExecutionStatus


class ExecutionTraceCollector:
    """Collect execution records during capability execution."""

    def __init__(
        self,
        execution_id: str,
    ) -> None:
        self._execution_id = execution_id
        self._records: list[
            CapabilityExecutionRecord
        ] = []

    def start(
        self,
        capability_id: str,
        capability_version: str,
    ) -> int:
        """Start tracking a capability execution."""

        record = CapabilityExecutionRecord(
            capability_id=capability_id,
            capability_version=capability_version,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(UTC),
        )

        self._records.append(record)

        return len(self._records) - 1


    def complete(
        self,
        index: int,
        outputs: Mapping[str, Any],
    ) -> None:
        """Mark capability execution as completed."""

        current = self._records[index]

        finished = datetime.now(UTC)

        duration = (
            finished - current.started_at
        ).total_seconds() * 1000

        self._records[index] = CapabilityExecutionRecord(
            capability_id=current.capability_id,
            capability_version=current.capability_version,
            status=ExecutionStatus.COMPLETED,
            started_at=current.started_at,
            finished_at=finished,
            duration_ms=duration,
            outputs=outputs,
        )


    def fail(
        self,
        index: int,
        error: Exception,
    ) -> None:
        """Mark capability execution as failed."""

        current = self._records[index]

        finished = datetime.now(UTC)

        duration = (
            finished - current.started_at
        ).total_seconds() * 1000

        self._records[index] = CapabilityExecutionRecord(
            capability_id=current.capability_id,
            capability_version=current.capability_version,
            status=ExecutionStatus.FAILED,
            started_at=current.started_at,
            finished_at=finished,
            duration_ms=duration,
            error=str(error),
        )


    def trace(self) -> ExecutionTrace:
        """Return immutable execution trace."""

        return ExecutionTrace(
            execution_id=self._execution_id,
            records=tuple(self._records),
        )


__all__ = [
    "ExecutionTraceCollector",
]