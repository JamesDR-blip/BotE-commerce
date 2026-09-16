"""Application service for autonomous-operation policy evaluation."""

from __future__ import annotations

from domain.autonomous_operations import (
    AutonomousDecision,
    AutonomousEvaluation,
    AutonomousPolicy,
)


class AutonomousOpsService:
    """Evaluate whether an operation may proceed autonomously."""

    def __init__(self, *, policy: AutonomousPolicy) -> None:
        self._policy = policy

    @property
    def policy(self) -> AutonomousPolicy:
        """Return the configured autonomous-operation policy."""
        return self._policy

    def evaluate(
        self,
        *,
        risk_score: str,
        blast_radius: float,
        affected_rows: int,
        changeset_items: int,
        operations: int = 1,
        iterations: int = 1,
        consecutive_failures: int = 0,
        confidence: float | None = None,
    ) -> AutonomousEvaluation:
        """Evaluate hard autonomous-operation limits."""
        if not 0.0 <= blast_radius <= 1.0:
            raise ValueError("blast_radius must be between 0 and 1")

        if affected_rows < 0:
            raise ValueError("affected_rows must be >= 0")

        if changeset_items < 0:
            raise ValueError("changeset_items must be >= 0")

        if operations < 0:
            raise ValueError("operations must be >= 0")

        if iterations < 0:
            raise ValueError("iterations must be >= 0")

        if consecutive_failures < 0:
            raise ValueError("consecutive_failures must be >= 0")

        if confidence is not None and not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if risk_score in {"HIGH", "CRITICAL"}:
            return AutonomousEvaluation(
                decision=AutonomousDecision.REQUIRE_APPROVAL,
                reason="risk score requires manual approval",
                risk_score=risk_score,
                confidence=confidence,
            )

        if affected_rows > self._policy.max_affected_rows:
            return AutonomousEvaluation(
                decision=AutonomousDecision.BLOCKED,
                reason="affected_rows exceeds autonomous policy limit",
                risk_score=risk_score,
                confidence=confidence,
            )

        if changeset_items > self._policy.max_changeset_items:
            return AutonomousEvaluation(
                decision=AutonomousDecision.BLOCKED,
                reason="changeset_items exceeds autonomous policy limit",
                risk_score=risk_score,
                confidence=confidence,
            )

        if operations > self._policy.max_operations:
            return AutonomousEvaluation(
                decision=AutonomousDecision.BLOCKED,
                reason="operations exceeds autonomous policy limit",
                risk_score=risk_score,
                confidence=confidence,
            )

        if iterations > self._policy.max_iterations:
            return AutonomousEvaluation(
                decision=AutonomousDecision.BLOCKED,
                reason="iterations exceeds autonomous policy limit",
                risk_score=risk_score,
                confidence=confidence,
            )

        if consecutive_failures > self._policy.max_consecutive_failures:
            return AutonomousEvaluation(
                decision=AutonomousDecision.BLOCKED,
                reason="consecutive_failures exceeds autonomous policy limit",
                risk_score=risk_score,
                confidence=confidence,
            )

        if blast_radius > self._policy.max_blast_radius:
            return AutonomousEvaluation(
                decision=AutonomousDecision.BLOCKED,
                reason="blast_radius exceeds autonomous policy limit",
                risk_score=risk_score,
                confidence=confidence,
            )
        if risk_score != "LOW":
            return AutonomousEvaluation(
                decision=AutonomousDecision.BLOCKED,
                reason="only LOW risk operations may be applied autonomously",
                risk_score=risk_score,
                confidence=confidence,
            )

        return AutonomousEvaluation(
            decision=AutonomousDecision.AUTO_APPLY,
            reason="operation satisfies autonomous policy",
            risk_score=risk_score,
            confidence=confidence,
        )



