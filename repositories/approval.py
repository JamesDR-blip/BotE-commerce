# repositories/approval.py
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from database.models import ApprovalRecord, RiskPolicyRecord
from domain.approval import ApprovalRequest, ApprovalDecision
from domain.risk import RiskPolicy

class ApprovalRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, request: ApprovalRequest) -> ApprovalRecord:
        created_at = request.created_at or datetime.now(timezone.utc)
        record = ApprovalRecord(
            approval_id=request.approval_id,
            execution_id=request.execution_id,
            risk_score=request.risk_score,
            confidence_score=request.confidence_score,
            requested_by=request.requested_by,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def update_decision(self, approval_id: str, decision: ApprovalDecision) -> Optional[ApprovalRecord]:
        record = self.session.query(ApprovalRecord).filter(ApprovalRecord.approval_id == approval_id).first()
        if not record:
            return None
        # Record status field or decision tracking
        self.session.commit()
        self.session.refresh(record)
        return record

    def get_by_id(self, approval_id: str) -> Optional[ApprovalRecord]:
        return self.session.query(ApprovalRecord).filter(ApprovalRecord.approval_id == approval_id).first()

    def get_by_execution_id(self, execution_id: str) -> List[ApprovalRecord]:
        return self.session.query(ApprovalRecord).filter(ApprovalRecord.execution_id == execution_id).all()


class RiskPolicyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_active_policy(self) -> RiskPolicy:
        record = self.session.query(RiskPolicyRecord).order_by(RiskPolicyRecord.id.desc()).first()
        if not record:
            return RiskPolicy()
        return RiskPolicy(
            high_risk_threshold=record.high_risk_threshold,
            critical_risk_threshold=record.critical_risk_threshold,
        )

    def save_policy(self, policy: RiskPolicy) -> RiskPolicyRecord:
        record = RiskPolicyRecord(
            high_risk_threshold=policy.high_risk_threshold,
            critical_risk_threshold=policy.critical_risk_threshold,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record