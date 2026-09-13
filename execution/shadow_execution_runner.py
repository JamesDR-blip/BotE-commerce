"""Ephemeral workflow execution runner for shadow simulation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping
from uuid import uuid4

try:
    import pandas as pd
except ImportError:  # pragma: no cover - project capabilities already require pandas
    pd = None

from domain.plans import ExecutionPlan
from domain.simulation import (
    DiffPreview,
    RowDiff,
    SimulationResult,
    TabularDiff,
)


class ShadowExecutionRunner:
    """Execute a workflow plan without production execution persistence."""

    def __init__(
        self,
        *,
        capability_execution,
        dataset_storage=None,
        streaming_reader=None,
    ) -> None:
        self._capability_execution = capability_execution
        self._dataset_storage = dataset_storage
        self._streaming_reader = streaming_reader

    def simulate(
        self,
        *,
        workflow_id: str,
        workflow_version: str,
        plan: ExecutionPlan,
        inputs: Mapping[str, Any],
        simulation_id: str | None = None,
        max_diff_rows: int = 100,
        dataset=None,
    ) -> SimulationResult:
        if max_diff_rows < 0:
            raise ValueError("max_diff_rows must be non-negative")

        simulation_id = simulation_id or str(uuid4())

        try:
            if self._is_streaming(plan):
                if dataset is None:
                    raise ValueError(
                        "Streaming workflow simulation requires a dataset"
                    )

                return self._simulate_streaming(
                    workflow_id=workflow_id,
                    workflow_version=workflow_version,
                    plan=plan,
                    inputs=inputs,
                    simulation_id=simulation_id,
                    max_diff_rows=max_diff_rows,
                    dataset=dataset,
                )

            return self._simulate_in_memory(
                workflow_id=workflow_id,
                workflow_version=workflow_version,
                plan=plan,
                inputs=inputs,
                simulation_id=simulation_id,
                max_diff_rows=max_diff_rows,
            )

        except Exception as exc:
            return SimulationResult(
                simulation_id=simulation_id,
                workflow_id=workflow_id,
                workflow_version=workflow_version,
                success=False,
                error=str(exc),
            )

    def _simulate_in_memory(
        self,
        *,
        workflow_id: str,
        workflow_version: str,
        plan: ExecutionPlan,
        inputs: Mapping[str, Any],
        simulation_id: str,
        max_diff_rows: int,
    ) -> SimulationResult:
        isolated_inputs = {
            key: self._isolate(value)
            for key, value in inputs.items()
        }

        result = self._capability_execution.execute_plan(
            plan=plan,
            inputs=isolated_inputs,
            execution_id=simulation_id,
        )

        outputs = {
            key: self._isolate(value)
            for key, value in result.outputs.items()
        }

        diff = self._build_diff(
            before=isolated_inputs,
            after=outputs,
            max_diff_rows=max_diff_rows,
        )

        return SimulationResult(
            simulation_id=simulation_id,
            workflow_id=workflow_id,
            workflow_version=workflow_version,
            outputs=outputs,
            diff=diff,
        )

    def _simulate_streaming(
        self,
        *,
        workflow_id: str,
        workflow_version: str,
        plan: ExecutionPlan,
        inputs: Mapping[str, Any],
        simulation_id: str,
        max_diff_rows: int,
        dataset,
    ) -> SimulationResult:
        if self._dataset_storage is None:
            raise RuntimeError(
                "Dataset storage is required for streaming simulation"
            )

        if self._streaming_reader is None:
            raise RuntimeError(
                "Streaming reader is required for streaming simulation"
            )

        if not dataset.storage_key:
            raise ValueError(
                f"Dataset has no persisted storage: {dataset.id}"
            )

        accumulator = _StreamingDiffAccumulator(
            max_diff_rows=max_diff_rows,
        )

        processed_chunks = 0
        processed_rows = 0

        with self._dataset_storage.open(
            storage_key=dataset.storage_key,
        ) as source:
            for chunk in self._streaming_reader.stream(
                dataset.filename,
                source,
            ):
                isolated_chunk = self._isolate(chunk)

                chunk_inputs = {
                    key: self._isolate(value)
                    for key, value in inputs.items()
                }
                chunk_inputs["frame"] = isolated_chunk

                result = self._capability_execution.execute_plan(
                    plan=plan,
                    inputs=chunk_inputs,
                    execution_id=simulation_id,
                )

                chunk_outputs = {
                    key: self._isolate(value)
                    for key, value in result.outputs.items()
                }

                accumulator.observe(
                    before=chunk_inputs,
                    after=chunk_outputs,
                )

                processed_chunks += 1

                processed_row_count = chunk_outputs.get(
                    "processed_rows"
                )

                if isinstance(processed_row_count, int):
                    processed_rows += processed_row_count
                else:
                    try:
                        processed_rows += len(chunk)
                    except TypeError as exc:
                        raise TypeError(
                            "Streaming reader chunks must support len()"
                        ) from exc

        return SimulationResult(
            simulation_id=simulation_id,
            workflow_id=workflow_id,
            workflow_version=workflow_version,
            outputs={
                "processed_chunks": processed_chunks,
                "processed_rows": processed_rows,
            },
            diff=accumulator.result(),
        )

    @staticmethod
    def _is_streaming(plan: ExecutionPlan) -> bool:
        execution_metadata = plan.metadata.get("execution", {})
        return execution_metadata.get("mode") == "streaming"

    @staticmethod
    def _isolate(value: Any) -> Any:
        if pd is not None and isinstance(value, pd.DataFrame):
            return value.copy(deep=True)

        if pd is not None and isinstance(value, pd.Series):
            return value.copy(deep=True)

        try:
            return deepcopy(value)
        except Exception:
            return value

    @classmethod
    def _build_diff(
        cls,
        *,
        before: Mapping[str, Any],
        after: Mapping[str, Any],
        max_diff_rows: int,
    ) -> DiffPreview:
        changed_keys = []
        tabular_diffs = []

        for key in sorted(set(before) | set(after)):
            before_value = before.get(key)
            after_value = after.get(key)

            if cls._dataframes_equal(before_value, after_value):
                continue

            changed_keys.append(key)

            if cls._is_dataframe(before_value) and cls._is_dataframe(after_value):
                tabular_diffs.append(
                    cls._dataframe_diff(
                        input_key=key,
                        before=before_value,
                        after=after_value,
                        max_diff_rows=max_diff_rows,
                    )
                )

        return DiffPreview(
            tabular=tuple(tabular_diffs),
            changed_keys=tuple(changed_keys),
        )

    @staticmethod
    def _is_dataframe(value: Any) -> bool:
        return pd is not None and isinstance(value, pd.DataFrame)

    @classmethod
    def _dataframes_equal(cls, before: Any, after: Any) -> bool:
        if cls._is_dataframe(before) and cls._is_dataframe(after):
            return before.equals(after)

        if cls._is_dataframe(before) or cls._is_dataframe(after):
            return False

        try:
            return before == after
        except Exception:
            return before is after

    @classmethod
    def _dataframe_diff(
        cls,
        *,
        input_key: str,
        before,
        after,
        max_diff_rows: int,
    ) -> TabularDiff:
        before_columns = tuple(str(column) for column in before.columns)
        after_columns = tuple(str(column) for column in after.columns)

        before_rows = len(before)
        after_rows = len(after)
        shared_rows = min(before_rows, after_rows)

        changed_rows = 0
        row_diffs: list[RowDiff] = []

        for index in range(shared_rows):
            before_row = before.iloc[index]
            after_row = after.iloc[index]

            if not cls._series_equal(before_row, after_row):
                changed_rows += 1

                if len(row_diffs) < max_diff_rows:
                    row_diffs.append(
                        RowDiff(
                            row_index=index,
                            before=before_row.to_dict(),
                            after=after_row.to_dict(),
                        )
                    )

        added_rows = max(0, after_rows - before_rows)
        removed_rows = max(0, before_rows - after_rows)

        if len(row_diffs) < max_diff_rows and removed_rows:
            for index in range(shared_rows, before_rows):
                if len(row_diffs) >= max_diff_rows:
                    break

                row_diffs.append(
                    RowDiff(
                        row_index=index,
                        before=before.iloc[index].to_dict(),
                        after=None,
                    )
                )

        if len(row_diffs) < max_diff_rows and added_rows:
            for index in range(shared_rows, after_rows):
                if len(row_diffs) >= max_diff_rows:
                    break

                row_diffs.append(
                    RowDiff(
                        row_index=index,
                        before=None,
                        after=after.iloc[index].to_dict(),
                    )
                )

        total_differences = (
            changed_rows + added_rows + removed_rows
        )

        return TabularDiff(
            input_key=input_key,
            before_rows=before_rows,
            after_rows=after_rows,
            before_columns=before_columns,
            after_columns=after_columns,
            added_rows=added_rows,
            removed_rows=removed_rows,
            changed_rows=changed_rows,
            row_diffs=tuple(row_diffs),
            truncated=total_differences > len(row_diffs),
        )

    @staticmethod
    def _series_equal(before, after) -> bool:
        try:
            return bool(before.equals(after))
        except Exception:
            return before.to_dict() == after.to_dict()


class _StreamingDiffAccumulator:
    """Bounded-memory diff accumulator for streaming simulation."""

    def __init__(self, *, max_diff_rows: int) -> None:
        self._max_diff_rows = max_diff_rows
        self._changed_keys: set[str] = set()
        self._tabular: dict[str, _TabularDiffAccumulator] = {}

    def observe(
        self,
        *,
        before: Mapping[str, Any],
        after: Mapping[str, Any],
    ) -> None:
        for key in sorted(set(before) | set(after)):
            before_value = before.get(key)
            after_value = after.get(key)

            if ShadowExecutionRunner._dataframes_equal(
                before_value,
                after_value,
            ):
                continue

            self._changed_keys.add(key)

            if (
                ShadowExecutionRunner._is_dataframe(before_value)
                and ShadowExecutionRunner._is_dataframe(after_value)
            ):
                accumulator = self._tabular.setdefault(
                    key,
                    _TabularDiffAccumulator(
                        input_key=key,
                        max_diff_rows=self._max_diff_rows,
                    ),
                )
                accumulator.observe(
                    before=before_value,
                    after=after_value,
                )

    def result(self) -> DiffPreview:
        return DiffPreview(
            tabular=tuple(
                accumulator.result()
                for _, accumulator in sorted(
                    self._tabular.items()
                )
            ),
            changed_keys=tuple(sorted(self._changed_keys)),
        )


class _TabularDiffAccumulator:
    """Accumulate row-level diff statistics without retaining all rows."""

    def __init__(
        self,
        *,
        input_key: str,
        max_diff_rows: int,
    ) -> None:
        self._input_key = input_key
        self._max_diff_rows = max_diff_rows

        self._before_rows = 0
        self._after_rows = 0
        self._before_columns: tuple[str, ...] = ()
        self._after_columns: tuple[str, ...] = ()

        self._added_rows = 0
        self._removed_rows = 0
        self._changed_rows = 0

        self._row_diffs: list[RowDiff] = []
        self._offset = 0

    def observe(self, *, before, after) -> None:
        self._before_rows += len(before)
        self._after_rows += len(after)

        self._before_columns = tuple(
            str(column) for column in before.columns
        )
        self._after_columns = tuple(
            str(column) for column in after.columns
        )

        shared_rows = min(len(before), len(after))

        for index in range(shared_rows):
            before_row = before.iloc[index]
            after_row = after.iloc[index]

            if not ShadowExecutionRunner._series_equal(
                before_row,
                after_row,
            ):
                self._changed_rows += 1

                if len(self._row_diffs) < self._max_diff_rows:
                    self._row_diffs.append(
                        RowDiff(
                            row_index=self._offset + index,
                            before=before_row.to_dict(),
                            after=after_row.to_dict(),
                        )
                    )

        removed = max(0, len(before) - len(after))
        added = max(0, len(after) - len(before))

        self._removed_rows += removed
        self._added_rows += added

        if removed and len(self._row_diffs) < self._max_diff_rows:
            for index in range(shared_rows, len(before)):
                if len(self._row_diffs) >= self._max_diff_rows:
                    break

                self._row_diffs.append(
                    RowDiff(
                        row_index=self._offset + index,
                        before=before.iloc[index].to_dict(),
                        after=None,
                    )
                )

        if added and len(self._row_diffs) < self._max_diff_rows:
            for index in range(shared_rows, len(after)):
                if len(self._row_diffs) >= self._max_diff_rows:
                    break

                self._row_diffs.append(
                    RowDiff(
                        row_index=self._offset + index,
                        before=None,
                        after=after.iloc[index].to_dict(),
                    )
                )

        self._offset += max(len(before), len(after))

    def result(self) -> TabularDiff:
        total_differences = (
            self._changed_rows
            + self._added_rows
            + self._removed_rows
        )

        return TabularDiff(
            input_key=self._input_key,
            before_rows=self._before_rows,
            after_rows=self._after_rows,
            before_columns=self._before_columns,
            after_columns=self._after_columns,
            added_rows=self._added_rows,
            removed_rows=self._removed_rows,
            changed_rows=self._changed_rows,
            row_diffs=tuple(self._row_diffs),
            truncated=total_differences > len(self._row_diffs),
        )


__all__ = ["ShadowExecutionRunner"]

