"""Repository for execution audit records."""
from __future__ import annotations

from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import (
    ExecutionRecord,
    ReportRecord,
    ValidationLogRecord,
)
from domain.models import ValidationIssue


class ExecutionRepository:
    def __init__(self, sessions: Callable[[], Session]) -> None:
        self._sessions = sessions

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
                    row_number=issue.row,
                    field=issue.field,
                    code=issue.code,
                    message=issue.message,
                    severity=issue.severity,
                )
                for issue in issues
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
            return list(
                session.scalars(
                    select(ExecutionRecord)
                    .order_by(ExecutionRecord.created_at.desc())
                    .limit(limit)
                )
            )

    def list_by_dataset(
        self,
        dataset_id: str,
        limit: int = 50,
    ) -> list[ExecutionRecord]:
        with self._sessions() as session:
            return list(
                session.scalars(
                    select(ExecutionRecord)
                    .where(ExecutionRecord.dataset_id == dataset_id)
                    .order_by(ExecutionRecord.created_at.desc())
                    .limit(limit)
                )
            )

    def list_validation_logs(
        self,
        execution_id: str,
    ) -> list[ValidationLogRecord]:
        with self._sessions() as session:
            return list(
                session.scalars(
                    select(ValidationLogRecord)
                    .where(
                        ValidationLogRecord.execution_id == execution_id
                    )
                    .order_by(ValidationLogRecord.id.asc())
                )
            )

    def get(self, execution_id: str) -> ExecutionRecord | None:
        with self._sessions() as session:
            return session.get(ExecutionRecord, execution_id)

    def report_path(
        self,
        execution_id: str,
        report_format: str,
    ) -> str | None:
        with self._sessions() as session:
            return session.scalar(
                select(ReportRecord.path).where(
                    ReportRecord.execution_id == execution_id,
                    ReportRecord.format == report_format,
                )
            )

    def save_execution_context(
        self,
        execution_id: str,
        *,
        requirement_json: str,
        plan_json: str,
        planner_version: str | None,
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

            record.requirement_json = requirement_json
            record.plan_json = plan_json
            record.planner_version = planner_version

            session.commit()

    def execution_context(
        self,
        execution_id: str,
    ) -> dict[str, str | None] | None:
        with self._sessions() as session:
            record = session.get(
                ExecutionRecord,
                execution_id,
            )

            if record is None:
                return None

            return {
                "requirement_json": record.requirement_json,
                "plan_json": record.plan_json,
                "planner_version": record.planner_version,
            }
