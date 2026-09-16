"""Domain contracts for autonomous operations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AutonomousDecision(str, Enum):
    """Decision produced by autonomous-operation governance."""

    AUTO_APPLY = "AUTO_APPLY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class AutonomousPolicy:
    """Hard limits governing autonomous operations."""

    max_operations: int = 1
    max_iterations: int = 1
    max_affected_rows: int = 100
    max_changeset_items: int = 100
    max_blast_radius: float = 0.1
    max_consecutive_failures: int = 1

    def __post_init__(self) -> None:
        if self.max_operations < 1:
            raise ValueError("max_operations must be >= 1")

        if self.max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")

        if self.max_affected_rows < 0:
            raise ValueError("max_affected_rows must be >= 0")

        if self.max_changeset_items < 0:
            raise ValueError("max_changeset_items must be >= 0")

        if not 0.0 <= self.max_blast_radius <= 1.0:
            raise ValueError(
                "max_blast_radius must be between 0 and 1"
            )

        if self.max_consecutive_failures < 0:
            raise ValueError(
                "max_consecutive_failures must be >= 0"
            )


@dataclass(frozen=True)
class AutonomousEvaluation:
    """Result of evaluating one autonomous operation."""

    decision: AutonomousDecision
    reason: str
    risk_score: str | None = None
    confidence: float | None = None
