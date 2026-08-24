"""Repository for validation execution trace persistence."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import (
    ExecutionRecord,
    ExecutionTraceRecord,
)


class ExecutionTraceRepository:
    def __init__(
        self,
        sessions: Callable[[], Session],
    ) -> None:
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
    ) -> ExecutionTraceRecord:
        with self._sessions() as session:
            execution = session.get(
                ExecutionRecord,
                execution_id,
            )

            if execution is None:
                raise ValueError(
                    f"Execution {execution_id} does not exist"
                )

            record = ExecutionTraceRecord(
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
    ) -> ExecutionTraceRecord:
        with self._sessions() as session:
            record = session.get(
                ExecutionTraceRecord,
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
    ) -> ExecutionTraceRecord:
        with self._sessions() as session:
            record = session.get(
                ExecutionTraceRecord,
                trace_id,
            )

            if record is None:
                raise ValueError(
                    f"Trace not found: {trace_id}"
                )

            record.status = "FAILED"
            record.outputs_json = json.dumps(
                {"error": error},
                default=str,
            )
            record.error = error
            record.finished_at = finished_at

            session.commit()
            session.refresh(record)

            return record

    def list_by_execution(
        self,
        execution_id: str,
    ) -> list[ExecutionTraceRecord]:
        with self._sessions() as session:
            return list(
                session.scalars(
                    select(ExecutionTraceRecord)
                    .where(
                        ExecutionTraceRecord.execution_id
                        == execution_id
                    )
                    .order_by(
                        ExecutionTraceRecord.started_at
                    )
                )
            )