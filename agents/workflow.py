"""Multi-agent data quality workflow. Agents never execute LLM-generated code."""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from repositories.rules import RuleRepository
from services.plugins import ValidatorRegistry
from services.anomalies import detect_anomalies
from services.health_score_service import HealthScoreService
from services.validation_service import ValidationService
from domain.models import ValidationIssue, ValidationResult
from rule_engine.models import RuleSet


class ClassifierAgent:
    def classify(self, frame: pd.DataFrame, choices: list[str], requested: str | None = None) -> str:
        if requested:
            if requested not in choices: raise ValueError(f"Unsupported category: {requested}")
            return requested
        columns = {str(c).casefold() for c in frame.columns}
        signals = {"Fashion": {"size", "color"}, "Cosmetics": {"volume", "ingredients"}, "HomeAppliances": {"power", "dimensions"}}
        column_scores = {category: len(columns & signals.get(category, set())) for category in choices}
        title_column = next((column for column in frame.columns if str(column).casefold() == "product_title"), None)
        if title_column is not None:
            appliance_terms = r"\b(?:fan|air fryer|humidifier|toothbrush|flosser|massager|printer|epilator|trimmer|appliance)\b"
            column_scores["HomeAppliances"] = column_scores.get("HomeAppliances", 0) + int(frame[title_column].fillna("").astype(str).str.contains(appliance_terms, case=False, regex=True).sum())
        return max(choices, key=lambda c: column_scores.get(c, 0))


class RuleRetrieverAgent:
    def __init__(self, repository: RuleRepository) -> None: self._repository = repository
    def retrieve(self, category: str) -> tuple[RuleSet, str]: return self._repository.get(category)


class AutoFixAgent:
    def fix(self, frame: pd.DataFrame, validator) -> pd.DataFrame: return validator.autofix(frame)


class ValidatorAgent:
    def __init__(self, service: ValidationService | None = None) -> None: self._service = service or ValidationService()
    def validate(self, frame: pd.DataFrame, validator, rules: RuleSet) -> list[ValidationIssue]:
        return self._service.validate(frame, validator, rules)


class QAAgent:
    def __init__(self, health_scores: HealthScoreService | None = None) -> None: self._health_scores = health_scores or HealthScoreService()
    def result(self, frame: pd.DataFrame, issues: list[ValidationIssue], category: str, version: str) -> ValidationResult:
        rejected_rows = {issue.row - 2 for issue in issues if issue.severity == "error"}
        rejected_rows |= detect_anomalies(frame)
        mask = frame.index.isin(rejected_rows); quarantine = frame.loc[mask].copy(); clean = frame.loc[~mask].copy()
        reason_map: dict[int, list[str]] = {}
        for issue in issues: reason_map.setdefault(issue.row - 2, []).append(issue.message)
        if not quarantine.empty:
            quarantine.insert(0, "_source_row", quarantine.index + 2)
            quarantine["_quarantine_reason"] = ["; ".join(reason_map.get(i, ["Statistical anomaly"])) for i in quarantine.index]
        score = self._health_scores.calculate(len(clean), len(frame))
        return ValidationResult(category, clean, quarantine, issues, score, version, len(rejected_rows - set(reason_map)))


class LLMExplanationAgent:
    """Optional explanation seam. Production adapters may call an LLM but return text only."""
    def explain(self, issues: list[ValidationIssue]) -> str:
        return f"Detected {len(issues)} deterministic validation issue(s)."


@dataclass
class Agents:
    classifier: ClassifierAgent; rules: RuleRetrieverAgent; fixer: AutoFixAgent; validator: ValidatorAgent; qa: QAAgent
