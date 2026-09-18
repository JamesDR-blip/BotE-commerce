from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CopilotApprovalCard:
    """Safe, presentation-level approval metadata for Copilot clients."""

    approval_id: str
    execution_id: str
    changeset_id: str
    risk_score: str
    confidence_score: float
    requested_by: str
    created_at: datetime
    expires_at: datetime | None
    status: str

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe presentation data without approval credentials."""
        return {
            "approval_id": self.approval_id,
            "execution_id": self.execution_id,
            "changeset_id": self.changeset_id,
            "risk_score": self.risk_score,
            "confidence_score": self.confidence_score,
            "requested_by": self.requested_by,
            "created_at": self.created_at.isoformat(),
            "expires_at": (
                self.expires_at.isoformat()
                if self.expires_at is not None
                else None
            ),
            "status": self.status,
        }

    @classmethod
    def from_record(cls, record: Any) -> "CopilotApprovalCard":
        return cls(
            approval_id=record.approval_id,
            execution_id=record.execution_id,
            changeset_id=record.changeset_id,
            risk_score=record.risk_score,
            confidence_score=record.confidence_score,
            requested_by=record.requested_by,
            created_at=record.created_at,
            expires_at=record.expires_at,
            status=record.decision or "PENDING",
        )

