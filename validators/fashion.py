"""Fashion category validator plugin."""
from __future__ import annotations
import pandas as pd
from models.domain import ValidationIssue
from validators.base import CategoryValidator


class FashionValidator(CategoryValidator):
    category = "Fashion"
    def autofix(self, frame: pd.DataFrame) -> pd.DataFrame:
        fixed = frame.copy()
        for column in fixed.columns:
            if column.casefold() == "size": fixed[column] = fixed[column].fillna("").astype(str).str.strip().str.upper()
            if column.casefold() == "color": fixed[column] = fixed[column].fillna("").astype(str).str.strip()
        return fixed
    def validate(self, frame: pd.DataFrame, rules: dict) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        names = {str(c).casefold(): c for c in frame.columns}
        for field in ("price", "size", "color"):
            if field not in names:
                issues.extend(ValidationIssue(i + 2, field, "missing_column", f"Missing required column: {field}") for i in range(len(frame)))
        if "price" in names:
            prices = pd.to_numeric(frame[names["price"]].astype(str).str.replace(r"[,.\s]", "", regex=True), errors="coerce")
            issues.extend(ValidationIssue(i + 2, "Price", "invalid_price", "Price must be a positive number") for i in prices.index[prices.isna() | (prices <= 0)])
        if "size" in names:
            valid = {"S", "M", "L", "XL", "XXL"}; values = frame[names["size"]].fillna("").astype(str)
            issues.extend(ValidationIssue(i + 2, "Size", "invalid_size", "Size must be S, M, L, XL or XXL") for i in values.index[~values.isin(valid)])
        if "color" in names:
            values = frame[names["color"]].fillna("").astype(str).str.strip()
            issues.extend(ValidationIssue(i + 2, "Color", "empty_color", "Color cannot be empty") for i in values.index[values.eq("")])
        return issues
