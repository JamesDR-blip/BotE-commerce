"""Domain contracts for workflow shadow simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RowDiff:
    """One positional row difference between before and after data."""

    row_index: int
    before: dict[str, Any] | None
    after: dict[str, Any] | None


@dataclass(frozen=True)
class TabularDiff:
    """Bounded structural diff for a tabular value."""

    input_key: str
    before_rows: int
    after_rows: int
    before_columns: tuple[str, ...]
    after_columns: tuple[str, ...]
    added_rows: int
    removed_rows: int
    changed_rows: int
    row_diffs: tuple[RowDiff, ...] = ()
    truncated: bool = False


@dataclass(frozen=True)
class DiffPreview:
    """Preview of observable tabular changes produced by simulation."""

    tabular: tuple[TabularDiff, ...] = ()
    changed_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class SimulationResult:
    """Ephemeral result of a workflow shadow execution."""

    simulation_id: str
    workflow_id: str
    workflow_version: str
    outputs: dict[str, Any] = field(default_factory=dict)
    diff: DiffPreview = field(default_factory=DiffPreview)
    success: bool = True
    error: str | None = None


__all__ = [
    "RowDiff",
    "TabularDiff",
    "DiffPreview",
    "SimulationResult",
]
