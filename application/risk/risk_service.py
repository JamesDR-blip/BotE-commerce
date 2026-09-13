from domain.risk import RiskPolicy, RiskScore, ConfidenceScore
from domain.risk_evaluation import RiskEvaluationResult

class RiskService:
    """Application service that evaluates risk for a pending mutation.

    It uses a configurable :class:`RiskPolicy` (default thresholds) to
    classify the *blast radius* of the operation and combines it with a
    confidence score (e.g., derived from data health). If the risk is HIGH
    or CRITICAL an approval is required.
    """

    def __init__(self, policy: RiskPolicy | None = None) -> None:
        # Use the default policy if none is supplied.
        self.policy = policy or RiskPolicy()

    def evaluate(self, blast_radius: float, confidence: float) -> RiskEvaluationResult:
        """Calculate the risk evaluation.

        Args:
            blast_radius: Normalised impact score in ``[0, 1]``.
            confidence: Confidence score in ``[0, 1]`` (e.g., from
                :class:`DataHealthScore.confidence_score`).
        Returns:
            :class:`RiskEvaluationResult` containing the categorical risk,
            confidence wrapper and a flag indicating whether approval is
            required.
        """
        if not 0.0 <= blast_radius <= 1.0:
            raise ValueError("blast_radius must be between 0 and 1")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        risk_score: RiskScore = self.policy.classify(blast_radius)
        confidence_obj = ConfidenceScore(confidence)
        approval_needed = risk_score in {RiskScore.HIGH, RiskScore.CRITICAL}
        return RiskEvaluationResult(
            risk_score=risk_score,
            confidence=confidence_obj,
            approval_required=approval_needed,
        )
