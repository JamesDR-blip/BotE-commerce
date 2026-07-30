"""Reusable deterministic format validation primitives."""
from __future__ import annotations

from collections.abc import Collection

import pandas as pd

from domain.models import ValidationIssue


class FormatValidation:
    """Validate values using existing numeric, enum, and regex semantics."""

    def positive_number(
        self,
        values: pd.Series,
        field: str,
        code: str,
        message: str,
        normalization_pattern: str | None = None,
        severity: str = "error",
    ) -> list[ValidationIssue]:
        normalized = values.fillna("").astype(str)
        if normalization_pattern:
            normalized = normalized.str.replace(normalization_pattern, "", regex=True)
        numeric = pd.to_numeric(normalized, errors="coerce")
        invalid = numeric.isna() | (numeric <= 0)
        return self._issues(values.index[invalid], field, code, message, severity)

    def enum(
        self,
        values: pd.Series,
        allowed_values: Collection[str],
        field: str,
        code: str,
        message: str,
        severity: str = "error",
    ) -> list[ValidationIssue]:
        invalid = ~values.fillna("").astype(str).isin(allowed_values)
        return self._issues(values.index[invalid], field, code, message, severity)

    def contains_regex(
        self,
        values: pd.Series,
        pattern: str,
        field: str,
        code: str,
        message: str,
        severity: str = "error",
    ) -> list[ValidationIssue]:
        invalid = ~values.fillna("").astype(str).str.contains(pattern, case=False, regex=True)
        return self._issues(values.index[invalid], field, code, message, severity)

    def matches_regex(
        self,
        values: pd.Series,
        pattern: str,
        field: str,
        code: str,
        message: str,
        severity: str = "error",
    ) -> list[ValidationIssue]:
        invalid = ~values.fillna("").astype(str).str.match(pattern, case=False)
        return self._issues(values.index[invalid], field, code, message, severity)

    @staticmethod
    def _issues(rows: pd.Index, field: str, code: str, message: str, severity: str) -> list[ValidationIssue]:
        return [ValidationIssue(int(row) + 2, field, code, message, severity) for row in rows]


__all__ = ["FormatValidation"]
