"""Reusable exact duplicate detection for normalized text values."""
from __future__ import annotations

import pandas as pd

from domain.models import ValidationIssue


class DuplicateDetection:
    """Detect exact duplicates after deterministic whitespace normalization."""

    def normalized_text_duplicates(
        self,
        values: pd.Series,
        field: str,
        code: str,
        message: str,
        severity: str = "error",
    ) -> list[ValidationIssue]:
        normalized = values.fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().str.casefold()
        duplicates = normalized.duplicated(keep="first")
        return [ValidationIssue(int(row) + 2, field, code, message, severity) for row in values.index[duplicates]]


__all__ = ["DuplicateDetection"]
