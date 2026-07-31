"""Quality-assurance agent that produces the existing validation result."""
from __future__ import annotations

import pandas as pd

from domain.models import ValidationIssue, ValidationResult
from services.anomalies import detect_anomalies
from services.health_score_service import HealthScoreService


class QAAgent:
    def __init__(self, health_scores: HealthScoreService | None = None) -> None:
        self._health_scores = health_scores or HealthScoreService()

    def result(self, frame: pd.DataFrame, issues: list[ValidationIssue], category: str, version: str) -> ValidationResult:
        rejected_rows = {issue.row - 2 for issue in issues if issue.severity == "error"}
        rejected_rows |= detect_anomalies(frame)
        mask = frame.index.isin(rejected_rows)
        quarantine, clean = frame.loc[mask].copy(), frame.loc[~mask].copy()
        reason_map: dict[int, list[str]] = {}
        for issue in issues:
            reason_map.setdefault(issue.row - 2, []).append(issue.message)
        if not quarantine.empty:
            quarantine.insert(0, "_source_row", quarantine.index + 2)
            quarantine["_quarantine_reason"] = ["; ".join(reason_map.get(index, ["Statistical anomaly"])) for index in quarantine.index]
        score = self._health_scores.calculate(len(clean), len(frame))
        return ValidationResult(category, clean, quarantine, issues, score, version, len(rejected_rows - set(reason_map)))
