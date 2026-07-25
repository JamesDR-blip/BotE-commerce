"""Cosmetics category validator plugin."""
from __future__ import annotations
import pandas as pd
from models.domain import ValidationIssue
from validators.base import CategoryValidator


class CosmeticsValidator(CategoryValidator):
    category = "Cosmetics"
    def validate(self, frame: pd.DataFrame, rules: dict) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        names = {str(c).casefold(): c for c in frame.columns}
        for key in ("volume", "ingredients"):
            if key not in names: issues.extend(ValidationIssue(i + 2, key, "missing_column", f"Missing required column: {key}") for i in range(len(frame)))
        if "volume" in names:
            values = frame[names["volume"]].fillna("").astype(str)
            issues.extend(ValidationIssue(i + 2, "Volume", "invalid_volume", "Volume needs ml or g") for i in values.index[~values.str.contains(r"\b\d+(?:[.,]\d+)?\s*(?:ml|g)\b", case=False, regex=True)])
        if "ingredients" in names:
            values = frame[names["ingredients"]].fillna("").astype(str).str.strip()
            issues.extend(ValidationIssue(i + 2, "Ingredients", "empty_ingredients", "Ingredients cannot be empty") for i in values.index[values.eq("")])
        return issues
