"""Domain models for multidimensional dataset health."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class HealthDimension(str, Enum):
    """Supported dimensions of dataset health."""

    COMPLETENESS = "completeness"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"


@dataclass(frozen=True)
class HealthMetric:
    """Score for one health dimension."""

    dimension: HealthDimension
    score: float
    assessed: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 100.0:
            raise ValueError("health score must be between 0 and 100")


@dataclass(frozen=True)
class DataHealthScore:
    """Multidimensional health score with an assessed-only aggregate."""

    metrics: tuple[HealthMetric, ...]

    @property
    def aggregate(self) -> float:
        assessed = tuple(
            metric.score
            for metric in self.metrics
            if metric.assessed
        )
        if not assessed:
            return 0.0
        return round(sum(assessed) / len(assessed), 2)

    @property
    def confidence_score(self) -> float:
        """Return the assessed-dimension ratio on a 0.0-1.0 scale."""

        if not self.metrics:
            return 0.0

        assessed_count = sum(
            1
            for metric in self.metrics
            if metric.assessed
        )
        return round(assessed_count / len(self.metrics), 4)

    def metric(self, dimension: HealthDimension) -> HealthMetric | None:
        return next(
            (
                metric
                for metric in self.metrics
                if metric.dimension == dimension
            ),
            None,
        )


@dataclass(frozen=True)
class IssueDiagnostic:
    """Sanitized diagnostic information safe for API exposure."""

    code: str
    field: str
    message: str
    severity: str
    count: int = 1

    def __post_init__(self) -> None:
        if self.count < 1:
            raise ValueError("diagnostic count must be positive")


@dataclass(frozen=True)
class RemediationProposal:
    """Read-only remediation proposal."""

    id: str
    diagnostic_code: str
    action: str
    rationale: str
    severity: str
    status: str = "PROPOSED"


def completeness_score(
    null_ratios: tuple[float, ...],
) -> float:
    """Calculate completeness from persisted column null ratios."""

    if not null_ratios:
        return 0.0

    score = 100.0 * (
        1.0 - sum(null_ratios) / len(null_ratios)
    )
    return round(max(0.0, min(100.0, score)), 2)


def uniqueness_score(
    row_count: int,
    duplicate_row_count: int,
) -> float:
    """Calculate uniqueness from persisted duplicate-row statistics."""

    if row_count <= 0:
        return 0.0

    duplicate_ratio = duplicate_row_count / row_count
    score = 100.0 * (1.0 - duplicate_ratio)
    return round(max(0.0, min(100.0, score)), 2)


__all__ = [
    "DataHealthScore",
    "HealthDimension",
    "HealthMetric",
    "IssueDiagnostic",
    "RemediationProposal",
    "completeness_score",
    "uniqueness_score",
]
