"""Repository for execution audit records."""
from __future__ import annotations
from typing import Callable
from sqlalchemy import select
from sqlalchemy.orm import Session
from database.models import ExecutionRecord, ReportRecord, ValidationLogRecord
from domain.models import ValidationIssue


class ExecutionRepository:
    def __init__(self, sessions: Callable[[], Session]) -> None: self._sessions = sessions
    def save(self, record: ExecutionRecord, issues: list[ValidationIssue], reports: dict[str, str]) -> None:
        with self._sessions() as session:
            session.add(record)
            session.add_all(ValidationLogRecord(execution_id=record.id, row_number=x.row, field=x.field, code=x.code, message=x.message, severity=x.severity) for x in issues)
            session.add_all(ReportRecord(execution_id=record.id, format=fmt, path=path) for fmt, path in reports.items())
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
