"""Repository for execution audit records."""
from __future__ import annotations
from typing import Callable
from sqlalchemy import select
from sqlalchemy.orm import Session
from database.models import (
    ExecutionRecord,
    ReportRecord,
    ValidationLogRecord,
    CapabilityExecutionTraceRecord,
)
from domain.models import ValidationIssue


class ExecutionRepository:
    def __init__(self, sessions: Callable[[], Session]) -> None: self._sessions = sessions

    def create(self, record: ExecutionRecord) -> None:
        with self._sessions() as session:
            session.add(record)
            session.commit()

    def update_status(self, execution_id: str, status: str) -> None:
        with self._sessions() as session:
            record = session.get(ExecutionRecord, execution_id)

            if record is None:
                raise KeyError(f"Execution not found: {execution_id}")

            record.status = status
            session.commit()

    def save_result(
        self,
        execution_id: str,
        category: str,
        source_hash: str,
        rule_version: str,
        health_score: float,
        issues: list[ValidationIssue],
        reports: dict[str, str],
    ) -> None:
        with self._sessions() as session:
            record = session.get(ExecutionRecord, execution_id)

            if record is None:
                raise ValueError(
                    f"Execution {execution_id} does not exist"
                )

            record.category = category
            record.source_hash = source_hash
            record.rule_version = rule_version
            record.health_score = health_score
            record.status = "COMPLETED"

            session.add_all(
                ValidationLogRecord(
                    execution_id=execution_id,
                    row_number=x.row,
                    field=x.field,
                    code=x.code,
                    message=x.message,
                    severity=x.severity,
                )
                for x in issues
            )

            session.add_all(
                ReportRecord(
                    execution_id=execution_id,
                    format=fmt,
                    path=path,
                )
                for fmt, path in reports.items()
            )

            session.commit()

    def history(self, limit: int = 50) -> list[ExecutionRecord]:
        with self._sessions() as session:
            return list(session.scalars(select(ExecutionRecord).order_by(ExecutionRecord.created_at.desc()).limit(limit)))

    def get(self, execution_id: str) -> ExecutionRecord | None:
        with self._sessions() as session:
            return session.get(ExecutionRecord, execution_id)

    def report_path(self, execution_id: str, report_format: str) -> str | None:
        with self._sessions() as session:
            return session.scalar(select(ReportRecord.path).where(ReportRecord.execution_id == execution_id, ReportRecord.format == report_format))

    def save_trace(
        self,
        execution_id: str,
        trace,
    ) -> None:
        with self._sessions() as session:
            record = session.get(
                ExecutionRecord,
                execution_id,
            )

            if record is None:
                raise ValueError(
                    f"Execution {execution_id} does not exist"
                )

            session.add_all(
                CapabilityExecutionTraceRecord(
                    execution_id=execution_id,
                    capability_id=item.capability_id,
                    capability_version=item.capability_version,
                    status=item.status.value
                    if hasattr(item.status, "value")
                    else str(item.status),
                    started_at=item.started_at,
                    finished_at=item.finished_at,
                    duration_ms=item.duration_ms,
                    error=item.error,
                    outputs_json=item.outputs or {},
                )
                for item in trace.records
            )

            session.commit()