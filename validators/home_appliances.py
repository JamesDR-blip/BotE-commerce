"""Home appliances category validator plugin."""
from __future__ import annotations
import pandas as pd
from models.domain import ValidationIssue
from validators.base import CategoryValidator


class HomeAppliancesValidator(CategoryValidator):
    category = "HomeAppliances"
    def validate(self, frame: pd.DataFrame, rules: dict) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        names = {str(c).casefold(): c for c in frame.columns}
        for key in ("power", "dimensions"):
            if key not in names: issues.extend(ValidationIssue(i + 2, key, "missing_column", f"Missing required column: {key}") for i in range(len(frame)))
        if "power" in names:
            vals = frame[names["power"]].fillna("").astype(str)
            issues.extend(ValidationIssue(i + 2, "Power", "invalid_power", "Power needs W or kW") for i in vals.index[~vals.str.contains(r"\b\d+(?:[.,]\d+)?\s*k?W\b", case=False, regex=True)])
        if "dimensions" in names:
            vals = frame[names["dimensions"]].fillna("").astype(str)
            pattern = r"^\s*\d+(?:[.,]\d+)?\s*[x×]\s*\d+(?:[.,]\d+)?\s*[x×]\s*\d+(?:[.,]\d+)?\s*(?:cm)?\s*$"
            issues.extend(ValidationIssue(i + 2, "Dimensions", "invalid_dimensions", "Dimensions need D x R x C (cm)") for i in vals.index[~vals.str.match(pattern, case=False)])
        return issues
