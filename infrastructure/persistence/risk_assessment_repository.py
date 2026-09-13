from __future__ import annotations

from typing import Callable

from sqlalchemy.orm import Session

from database.models import RiskAssessmentRecord


class RiskAssessmentRepository:
    """Persistence boundary for workflow execution risk assessments."""

    def __init__(self, sessions: Callable[[], Session]) -> None:
        self._sessions = sessions

    def create(
        self,
        *,
        assessment_id: str,
        execution_id: str,
        risk_score: str,
        confidence_score: float,
        approval_required: bool,
    ) -> RiskAssessmentRecord:
        with self._sessions() as session:
            record = RiskAssessmentRecord(
                id=assessment_id,
                execution_id=execution_id,
                risk_score=risk_score,
                confidence_score=confidence_score,
                approval_required=approval_required,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def get(self, assessment_id: str) -> RiskAssessmentRecord | None:
        with self._sessions() as session:
            return session.get(
                RiskAssessmentRecord,
                assessment_id,
            )

    def get_for_execution(
        self,
        execution_id: str,
    ) -> RiskAssessmentRecord | None:
        with self._sessions() as session:
            return (
                session.query(RiskAssessmentRecord)
                .filter(
                    RiskAssessmentRecord.execution_id == execution_id
                )
                .order_by(RiskAssessmentRecord.created_at.desc())
                .first()
            )
