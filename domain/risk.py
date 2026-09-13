from enum import Enum
from dataclasses import dataclass


class RiskScore(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class ConfidenceScore:
    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("confidence score must be between 0 and 1")


@dataclass(frozen=True)
class RiskPolicy:
    high_risk_threshold: float = 0.7
    critical_risk_threshold: float = 0.9

    def __post_init__(self) -> None:
        if not 0.0 <= self.high_risk_threshold <= 1.0:
            raise ValueError("high risk threshold must be between 0 and 1")
        if not 0.0 <= self.critical_risk_threshold <= 1.0:
            raise ValueError("critical risk threshold must be between 0 and 1")
        if self.high_risk_threshold > self.critical_risk_threshold:
            raise ValueError(
                "high risk threshold cannot exceed critical risk threshold"
            )

    def classify(self, blast_radius: float) -> RiskScore:
        if not 0.0 <= blast_radius <= 1.0:
            raise ValueError("blast radius must be between 0 and 1")
        if blast_radius >= self.critical_risk_threshold:
            return RiskScore.CRITICAL
        if blast_radius >= self.high_risk_threshold:
            return RiskScore.HIGH
        if blast_radius >= 0.4:
            return RiskScore.MEDIUM
        return RiskScore.LOW


__all__ = [
    "ConfidenceScore",
    "RiskPolicy",
    "RiskScore",
]
