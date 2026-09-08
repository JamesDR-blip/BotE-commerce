"""Persistence adapter for execution traces."""

from __future__ import annotations


class ExecutionTracePersistence:
    def __init__(
        self,
        repository,
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
                status=(
                    record.status.value
                    if hasattr(record.status, "value")
                    else str(record.status)
                ),
                inputs=dict(record.inputs)
                if record.inputs is not None
                else None,
                started_at=record.started_at,
            )

            status = (
                record.status.value
                if hasattr(record.status, "value")
                else str(record.status)
            )

            if status == "COMPLETED":
                self.repository.complete(
                    trace_id=item.id,
                    outputs=dict(record.outputs),
                    finished_at=record.finished_at,
                )

            elif status == "FAILED":
                self.repository.fail(
                    trace_id=item.id,
                    error=record.error or "",
                    finished_at=record.finished_at,
                )