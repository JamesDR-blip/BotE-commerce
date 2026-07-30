"""Typed rule-engine value objects."""
from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

RuleType = Literal["required_column", "positive_number", "enum", "non_empty", "regex"]


@dataclass(frozen=True)
class RuleDefinition:
    """One safe, declarative validation rule loaded from YAML."""

    type: RuleType
    field: str
    code: str
    message: str
    issue_field: str | None = None
    severity: str = "error"
    values: tuple[str, ...] = ()
    pattern: str | None = None
    normalization_pattern: str | None = None


@dataclass(frozen=True)
class RuleSet(Mapping[str, Any]):
    """Parsed rules while retaining read-only legacy mapping access."""

    category: str
    rules: tuple[RuleDefinition, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        return self.raw[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.raw)

    def __len__(self) -> int:
        return len(self.raw)


__all__ = ["RuleDefinition", "RuleSet", "RuleType"]
