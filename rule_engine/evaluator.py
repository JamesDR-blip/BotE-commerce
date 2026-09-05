"""Service that applies declarative YAML business rules."""
from __future__ import annotations

import pandas as pd

from domain.models import ValidationIssue
from rule_engine.models import RuleDefinition, RuleSet
from domain.validation.format import FormatValidation
from domain.validation.missing_values import MissingValueValidation


class BusinessRuleValidation:
    """Dispatch safe rule types to reusable validation services."""

    def __init__(self, missing_values: MissingValueValidation | None = None, formats: FormatValidation | None = None) -> None:
        self._missing_values = missing_values or MissingValueValidation()
        self._formats = formats or FormatValidation()

    def validate(self, frame: pd.DataFrame, rules: RuleSet) -> list[ValidationIssue]:
        names = {str(column).casefold(): column for column in frame.columns}
        issues: list[ValidationIssue] = []
        for rule in rules.rules:
            issues.extend(self._validate_rule(frame, names, rule))
        return issues

    def _validate_rule(self, frame: pd.DataFrame, names: dict[str, object], rule: RuleDefinition) -> list[ValidationIssue]:
        column = names.get(rule.field.casefold())
        if rule.type == "required_column":
            return [] if column is not None else self._missing_values.missing_column(frame, rule.field, rule.code, rule.message, rule.severity)
        if column is None:
            return []
        values = frame[column]
        field = rule.issue_field or rule.field
        if rule.type == "positive_number":
            return self._formats.positive_number(values, field, rule.code, rule.message, rule.normalization_pattern, rule.severity)
        if rule.type == "enum":
            return self._formats.enum(values, rule.values, field, rule.code, rule.message, rule.severity)
        if rule.type == "non_empty":
            return self._missing_values.non_empty(values, field, rule.code, rule.message, rule.severity)
        if rule.type == "regex":
            return self._formats.contains_regex(values, rule.pattern or "", field, rule.code, rule.message, rule.severity)
        return []


__all__ = ["BusinessRuleValidation"]
