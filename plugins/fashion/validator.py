"""Fashion category validator plugin."""
from __future__ import annotations
import pandas as pd
from domain.models import ValidationIssue
from plugins.base import ValidatorPlugin
from rule_engine.models import RuleSet
from rule_engine.validator import RuleValidator


class FashionValidator(ValidatorPlugin):
    category = "Fashion"
    def autofix(self, frame: pd.DataFrame) -> pd.DataFrame:
        fixed = frame.copy()
        for column in fixed.columns:
            if column.casefold() == "size": fixed[column] = fixed[column].fillna("").astype(str).str.strip().str.upper()
            if column.casefold() == "color": fixed[column] = fixed[column].fillna("").astype(str).str.strip()
        return fixed
    def validate(self, frame: pd.DataFrame, rules: RuleSet | dict[str, object]) -> list[ValidationIssue]:
        return RuleValidator().validate(frame, rules)
