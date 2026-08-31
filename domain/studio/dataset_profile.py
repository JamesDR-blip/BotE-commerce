"""Dataset profile domain models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnProfile:
    """Deterministic profile of a single dataset column."""

    name: str
    dtype: str
    null_count: int
    null_ratio: float
    unique_count: int
    sample_values: tuple[object, ...]


@dataclass(frozen=True)
class DatasetProfile:
    """Deterministic structural profile of a dataset."""

    row_count: int
    column_count: int
    duplicate_row_count: int
    columns: tuple[ColumnProfile, ...]