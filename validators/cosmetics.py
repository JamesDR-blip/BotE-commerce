"""Cosmetics category validator plugin."""
from __future__ import annotations
import pandas as pd
from domain.models import ValidationIssue
from services.format_validation import FormatValidation
from services.missing_value_validation import MissingValueValidation
from validators.base import CategoryValidator


class CosmeticsValidator(CategoryValidator):
    category = "Cosmetics"
    def validate(self, frame: pd.DataFrame, rules: dict) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        names = {str(c).casefold(): c for c in frame.columns}
        missing_values = MissingValueValidation(); formats = FormatValidation()
        for key in ("volume", "ingredients"):
            if key not in names:
                issues.extend(missing_values.missing_column(frame, key, "missing_column", f"Missing required column: {key}"))
        if "volume" in names:
            issues.extend(formats.contains_regex(frame[names["volume"]], r"\b\d+(?:[.,]\d+)?\s*(?:ml|g)\b", "Volume", "invalid_volume", "Volume needs ml or g"))
        if "ingredients" in names:
            issues.extend(missing_values.non_empty(frame[names["ingredients"]], "Ingredients", "empty_ingredients", "Ingredients cannot be empty"))
        return issues
