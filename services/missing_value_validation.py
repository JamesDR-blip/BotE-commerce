"""Reusable missing-column and empty-value validation."""
from __future__ import annotations

import pandas as pd

from domain.models import ValidationIssue


class MissingValueValidation:
    """Create the existing missing-value issue shapes without business rules."""

    def missing_column(
        self,
        frame: pd.DataFrame,
        field: str,
        code: str,
        message: str,
        severity: str = "error",
        use_frame_index: bool = False,
    ) -> list[ValidationIssue]:
        rows = frame.index if use_frame_index else range(len(frame))
        return [ValidationIssue(int(row) + 2, field, code, message, severity) for row in rows]

    def non_empty(
        self,
        values: pd.Series,
        field: str,
        code: str,
        message: str,
        severity: str = "error",
    ) -> list[ValidationIssue]:
        empty = values.fillna("").astype(str).str.strip().eq("")
        return [ValidationIssue(int(row) + 2, field, code, message, severity) for row in values.index[empty]]


__all__ = ["MissingValueValidation"]
