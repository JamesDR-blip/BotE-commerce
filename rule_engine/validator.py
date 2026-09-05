"""Deterministic dataframe validation for typed rule definitions."""
from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from domain.models import ValidationIssue
from rule_engine.models import RuleSet
from rule_engine.evaluator import BusinessRuleValidation


class RuleValidator:
    """Backward-compatible facade for declarative business-rule validation."""

    def __init__(self, service: BusinessRuleValidation | None = None) -> None:
        self._service = service or BusinessRuleValidation()

    def validate(self, frame: pd.DataFrame, rules: RuleSet | Mapping[str, object]) -> list[ValidationIssue]:
        return self._service.validate(frame, rules) if isinstance(rules, RuleSet) else []


__all__ = ["RuleValidator"]
