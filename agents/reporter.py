"""Reporting agent that delegates rendering to the stable report generator."""
from __future__ import annotations

from domain.models import ValidationResult
from reports.generator import ReportAgent


class ReporterAgent:
    """Publish reports; it does not interpret or execute generated content."""

    def __init__(self, reports: ReportAgent) -> None:
        self._reports = reports

    def generate(self, execution_id: str, result: ValidationResult) -> dict[str, str]:
        return self._reports.generate(execution_id, result)
