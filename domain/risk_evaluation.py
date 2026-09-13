from dataclasses import dataclass
from domain.risk import RiskScore, ConfidenceScore
from domain.approval import ApprovalRequest, ApprovalDecision

@dataclass(frozen=True)
class RiskEvaluationResult:
    """Result of risk evaluation for a pending mutation.

    - `risk_score`: categorical risk (LOW, MEDIUM, HIGH, CRITICAL).
    - `confidence`: confidence score (0.0‑1.0) derived from health metrics.
    - `approval_required`: True when risk is HIGH or CRITICAL and must go through approval.
    """
    risk_score: RiskScore
    confidence: ConfidenceScore
    approval_required: bool
