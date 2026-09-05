"""Health-score calculation isolated from result assembly."""
from __future__ import annotations


class HealthScoreService:
    """Preserve the platform's existing clean-row health-score formula."""

    def calculate(self, clean_records: int, total_records: int) -> float:
        return round(100 * clean_records / total_records, 2) if total_records else 0.0


__all__ = ["HealthScoreService"]
