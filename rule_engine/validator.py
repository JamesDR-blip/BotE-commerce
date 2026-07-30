"""Deterministic dataframe validation for typed rule definitions."""
from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from domain.models import ValidationIssue
from rule_engine.models import RuleDefinition, RuleSet


class RuleValidator:
    """Evaluate supported declarative rules without executing generated code."""

    def validate(self, frame: pd.DataFrame, rules: RuleSet | Mapping[str, object]) -> list[ValidationIssue]:
        if not isinstance(rules, RuleSet):
            return []
        names = {str(column).casefold(): column for column in frame.columns}
        issues: list[ValidationIssue] = []
        for rule in rules.rules:
            issues.extend(self._validate_rule(frame, names, rule))
        return issues

    def _validate_rule(self, frame: pd.DataFrame, names: dict[str, object], rule: RuleDefinition) -> list[ValidationIssue]:
        column = names.get(rule.field.casefold())
        if rule.type == "required_column":
            return self._missing_column_issues(frame, rule) if column is None else []
        if column is None:
            return []
        values = frame[column].fillna("").astype(str)
        field = rule.issue_field or rule.field
        if rule.type == "positive_number":
            if rule.normalization_pattern:
                values = values.str.replace(rule.normalization_pattern, "", regex=True)
            numeric = pd.to_numeric(values, errors="coerce")
            invalid = numeric.isna() | (numeric <= 0)
        elif rule.type == "enum":
            invalid = ~values.isin(rule.values)
        elif rule.type == "non_empty":
            invalid = values.str.strip().eq("")
        elif rule.type == "regex":
            invalid = ~values.str.contains(rule.pattern or "", case=False, regex=True)
        else:
            return []
        return [
            ValidationIssue(int(index) + 2, field, rule.code, rule.message, rule.severity)
            for index in values.index[invalid]
        ]

    @staticmethod
    def _missing_column_issues(frame: pd.DataFrame, rule: RuleDefinition) -> list[ValidationIssue]:
        return [
            ValidationIssue(index + 2, rule.field, rule.code, rule.message, rule.severity)
            for index in range(len(frame))
        ]


__all__ = ["RuleValidator"]
