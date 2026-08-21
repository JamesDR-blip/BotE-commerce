"""Repository for capability execution trace persistence."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import CapabilityExecutionTraceRecord


class CapabilityExecutionTraceRepository:

    def __init__(
        self,
        sessions,
    ):
        self._sessions = sessions


    def create_many(
        self,
        *,
        execution_id: str,
        records,
    ):
        with self._sessions() as session:

            for record in records:

                item = CapabilityExecutionTraceRecord(
                    execution_id=execution_id,
                    capability_id=record.capability_id,
                    capability_version=record.capability_version,
                    status=record.status.value,
                    inputs_json=json.dumps(
                        record.inputs,
                        default=str,
                    ),
                    outputs_json=json.dumps(
                        record.outputs,
                        default=str,
                    ),
                    started_at=record.started_at,
                    finished_at=record.finished_at,
                )

                session.add(item)

            session.commit()


    def create(
        self,
        *,
        execution_id: str,
        capability_id: str,
        capability_version: str,
        status: str,
        inputs: dict | None = None,
        started_at: datetime | None = None,
    ) -> CapabilityExecutionTraceRecord:

        with self._sessions() as session:

            record = CapabilityExecutionTraceRecord(
                execution_id=execution_id,
                capability_id=capability_id,
                capability_version=capability_version,
                status=status,
                inputs_json=json.dumps(
                    inputs or {},
                    default=str,
                ),
                started_at=started_at,
            )

            session.add(record)
            session.commit()
            session.refresh(record)

            return record


    def complete(
        self,
        *,
        trace_id: str,
        outputs: dict,
        finished_at: datetime,
    ) -> CapabilityExecutionTraceRecord:

        with self._sessions() as session:

            record = session.get(
                CapabilityExecutionTraceRecord,
                trace_id,
            )

            if record is None:
                raise ValueError(
                    f"Trace not found: {trace_id}"
                )

            record.status = "COMPLETED"
            record.outputs_json = json.dumps(
                outputs,
                default=str,
            )
            record.finished_at = finished_at

            session.commit()
            session.refresh(record)

            return record


    def fail(
        self,
        *,
        trace_id: str,
        error: str,
        finished_at: datetime,
    ) -> CapabilityExecutionTraceRecord:

        with self._sessions() as session:

            record = session.get(
                CapabilityExecutionTraceRecord,
                trace_id,
            )

            if record is None:
                raise ValueError(
                    f"Trace not found: {trace_id}"
                )

            record.status = "FAILED"
            record.outputs_json = json.dumps(
                {
                    "error": error
                }
            )
            record.finished_at = finished_at

            session.commit()
            session.refresh(record)

            return record

    def save(
        self,
        *,
        execution_id: str,
        trace,
    ) -> None:

        with self._sessions() as session:

            records = [
                CapabilityExecutionTraceRecord(
                    execution_id=execution_id,
                    capability_id=record.capability_id,
                    capability_version=record.capability_version,
                    status=(
                        record.status.value
                        if hasattr(
                            record.status,
                            "value",
                        )
                        else str(record.status)
                    ),
                    inputs_json=json.dumps(
                        record.inputs,
                        default=str,
                    )
                    if record.inputs is not None
                    else None,
                    outputs_json=json.dumps(
                        record.outputs,
                        default=str,
                    )
                    if record.outputs is not None
                    else None,
                    started_at=record.started_at,
                    finished_at=record.finished_at,
                    duration_ms=record.duration_ms,
                )
                for record in trace.records
            ]

            session.add_all(records)

            session.commit()

    def list_by_execution(
        self,
        execution_id: str,
    ):
        with self._sessions() as session:

            return list(
                session.scalars(
                    select(
                        CapabilityExecutionTraceRecord
                    )
                    .where(
                        CapabilityExecutionTraceRecord.execution_id
                        == execution_id
                    )
                    .order_by(
                        CapabilityExecutionTraceRecord.started_at
                    )
                )
            )

__all__ = [
    "CapabilityExecutionTraceRepository",
]