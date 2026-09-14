from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ApprovalDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class ApprovalRequest:
    approval_id: str
    execution_id: str
    changeset_id: str
    risk_score: str
    confidence_score: float
    requested_by: str
    created_at: datetime
    expires_at: datetime | None = None


__all__ = ["ApprovalDecision", "ApprovalRequest"]
