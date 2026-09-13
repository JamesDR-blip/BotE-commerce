from datetime import datetime, timezone
from typing import Callable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import ApprovalRecord
from domain.approval import ApprovalDecision, ApprovalRequest


class ApprovalRepository:
    def __init__(self, sessions: Callable[[], Session]):
        self._sessions = sessions

    def create(
        self,
        request: ApprovalRequest,
        *,
        token_hash: str,
    ) -> ApprovalRecord:
        created_at = request.created_at or datetime.now(timezone.utc)

        with self._sessions() as session:
            record = ApprovalRecord(
                approval_id=request.approval_id,
                execution_id=request.execution_id,
                risk_score=request.risk_score,
                confidence_score=request.confidence_score,
                requested_by=request.requested_by,
                created_at=created_at,
                expires_at=request.expires_at,
                decision=None,
                token_hash=token_hash,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def update_decision(
        self,
        approval_id: str,
        decision: ApprovalDecision,
    ) -> None:
        with self._sessions() as session:
            record = session.get(ApprovalRecord, approval_id)
            if record is None:
                raise ValueError(f"Approval {approval_id} not found")

            if record.decision is not None:
                raise ValueError(
                    f"Approval {approval_id} has already been decided"
                )

            now = datetime.now(timezone.utc)

            if record.expires_at is not None:
                expires_at = record.expires_at
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)

                if expires_at <= now:
                    record.decision = ApprovalDecision.EXPIRED.value
                    session.commit()
                    raise ValueError(
                        f"Approval {approval_id} has expired"
                    )

            if decision == ApprovalDecision.EXPIRED:
                raise ValueError(
                    "EXPIRED is not a caller-selectable approval decision"
                )

            record.decision = decision.value
            session.commit()

    def get(self, approval_id: str) -> Optional[ApprovalRecord]:
        with self._sessions() as session:
            return session.get(ApprovalRecord, approval_id)

    def list_pending(self) -> list[ApprovalRecord]:
        with self._sessions() as session:
            statement = (
                select(ApprovalRecord)
                .where(ApprovalRecord.decision.is_(None))
                .order_by(ApprovalRecord.created_at.asc())
            )
            return list(session.scalars(statement).all())
