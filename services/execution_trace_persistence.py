"""Persistence adapter for execution traces."""

from __future__ import annotations

from services.execution_trace_collector import ExecutionTraceCollector
from repositories.capability_execution_traces import (
    CapabilityExecutionTraceRepository,
)


class ExecutionTracePersistence:
    def __init__(
        self,
        repository: CapabilityExecutionTraceRepository,
    ) -> None:
        self.repository = repository


    def save(
        self,
        trace,
    ) -> None:

        for record in trace.records:

            item = self.repository.create(
                execution_id=trace.execution_id,
                capability_id=record.capability_id,
                capability_version=record.capability_version,
                status=record.status.value,
                inputs=dict(record.inputs),
                started_at=record.started_at,
            )

            if record.status.value == "COMPLETED":

                self.repository.complete(
                    trace_id=item.id,
                    outputs=dict(record.outputs),
                    finished_at=record.finished_at,
                )

            elif record.status.value == "FAILED":

                self.repository.fail(
                    trace_id=item.id,
                    error=record.error or "",
                    finished_at=record.finished_at,
                )