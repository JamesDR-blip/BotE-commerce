"""Deterministic dataset profiling service."""

from __future__ import annotations

import pandas as pd

from domain.studio.dataset_profile import ColumnProfile, DatasetProfile


class DatasetProfileService:
    """Build a deterministic structural profile from a DataFrame."""

    def __init__(self, sample_size: int = 5) -> None:
        if sample_size <= 0:
            raise ValueError("sample_size must be positive")

        self.sample_size = sample_size

    def profile(self, frame: pd.DataFrame) -> DatasetProfile:
        """Return a structural profile without mutating the input frame."""

        row_count = len(frame)
        column_count = len(frame.columns)

        duplicate_row_count = int(
            frame.duplicated(keep="first").sum()
        )

        columns = tuple(
            self._profile_column(frame[column])
            for column in frame.columns
        )

        return DatasetProfile(
            row_count=row_count,
            column_count=column_count,
            duplicate_row_count=duplicate_row_count,
            columns=columns,
        )

    def _profile_column(
        self,
        column: pd.Series,
    ) -> ColumnProfile:
        null_count = int(column.isna().sum())
        row_count = len(column)

        null_ratio = (
            null_count / row_count
            if row_count
            else 0.0
        )

        unique_count = int(
            column.nunique(dropna=False)
        )

        sample_values = tuple(
            column.drop_duplicates()
            .head(self.sample_size)
            .tolist()
        )

        return ColumnProfile(
            name=str(column.name),
            dtype=str(column.dtype),
            null_count=null_count,
            null_ratio=null_ratio,
            unique_count=unique_count,
            sample_values=sample_values,
        )