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
                workflow_execution_id=execution_id,
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
            record.error = error
            record.outputs_json = json.dumps(
                {
                    "error": error
                }
            )
            record.finished_at = finished_at

            session.commit()
            session.refresh(record)

            return record

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
                        CapabilityExecutionTraceRecord.workflow_execution_id
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