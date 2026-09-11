"""Exact streaming dataset profiling."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

import pandas as pd

from domain.studio.dataset_profile import ColumnProfile, DatasetProfile


@dataclass
class _ColumnState:
    name: str
    dtype: str
    null_count: int
    values: set[Any]
    samples: deque[Any]


class StreamingProfileAccumulator:
    """Accumulate an exact DatasetProfile from DataFrame chunks.

    The accumulator preserves the semantics of DatasetProfileService:
    exact row counts, duplicate counts, null counts, unique counts, and
    deterministic first-seen distinct sample values.

    Exact unique and duplicate tracking may grow with dataset cardinality.
    Chunk memory is bounded, but this class does not claim a hard global
    memory ceiling.
    """

    def __init__(self, sample_size: int = 5) -> None:
        if sample_size <= 0:
            raise ValueError("sample_size must be positive")

        self.sample_size = sample_size
        self._row_count = 0
        self._duplicate_row_count = 0
        self._columns: list[_ColumnState] | None = None
        self._row_signatures: set[Any] = set()

    def update(self, frame: pd.DataFrame) -> None:
        """Consume one DataFrame chunk."""
        if self._columns is None:
            self._initialize_columns(frame)
        elif list(frame.columns) != [column.name for column in self._columns]:
            raise ValueError("Chunk columns do not match previous chunks")

        for index, state in enumerate(self._columns):
            state.dtype = str(
                pd.concat(
                    [
                        pd.Series([], dtype=state.dtype),
                        frame.iloc[:, index],
                    ],
                    ignore_index=True,
                ).dtype
            )

        if frame.empty:
            return

        for _, row in frame.iterrows():
            signature = tuple(
                self._canonical_value(row.iloc[index])
                for index in range(len(self._columns))
            )

            if signature in self._row_signatures:
                self._duplicate_row_count += 1
            else:
                self._row_signatures.add(signature)

        for index, state in enumerate(self._columns):
            column = frame.iloc[:, index]

            state.null_count += int(column.isna().sum())

            for value in column:
                canonical = self._canonical_value(value)
                state.values.add(canonical)

                if (
                    len(state.samples) < self.sample_size
                    and canonical not in {
                        self._canonical_value(sample)
                        for sample in state.samples
                    }
                ):
                    state.samples.append(value)

        self._row_count += len(frame)

    def finalize(self) -> DatasetProfile:
        """Return the accumulated exact dataset profile."""
        if self._columns is None:
            return DatasetProfile(
                row_count=0,
                column_count=0,
                duplicate_row_count=0,
                columns=(),
            )

        columns = tuple(
            ColumnProfile(
                name=state.name,
                dtype=state.dtype,
                null_count=state.null_count,
                null_ratio=(
                    state.null_count / self._row_count
                    if self._row_count
                    else 0.0
                ),
                unique_count=len(state.values),
                sample_values=tuple(state.samples),
            )
            for state in self._columns
        )

        return DatasetProfile(
            row_count=self._row_count,
            column_count=len(self._columns),
            duplicate_row_count=self._duplicate_row_count,
            columns=columns,
        )

    def _initialize_columns(self, frame: pd.DataFrame) -> None:
        self._columns = [
            _ColumnState(
                name=str(column),
                dtype=str(frame[column].dtype),
                null_count=0,
                values=set(),
                samples=deque(maxlen=self.sample_size),
            )
            for column in frame.columns
        ]

    @staticmethod
    def _canonical_value(value: object) -> Any:
        if pd.isna(value):
            return ("__NULL__",)

        try:
            hash(value)
        except TypeError:
            return ("__UNHASHABLE__", repr(value))

        return ("__VALUE__", value)


__all__ = ["StreamingProfileAccumulator"]
