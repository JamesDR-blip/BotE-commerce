"""Framework-independent domain value objects."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import pandas as pd


@dataclass(frozen=True)
class ValidationIssue:
    row: int
    field: str
    code: str
    message: str
    severity: str = "error"


@dataclass
class ValidationResult:
    category: str
    clean: pd.DataFrame
    quarantine: pd.DataFrame
    issues: list[ValidationIssue]
    health_score: float
    rule_version: str
    anomaly_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionSummary:
    execution_id: str
    category: str
    health_score: float
    report_paths: dict[str, str]
    cached: bool = False
