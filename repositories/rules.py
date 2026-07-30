"""Backward-compatible repository facade for the YAML rule loader."""
from __future__ import annotations
from pathlib import Path

from rule_engine.loader import RuleLoader
from rule_engine.models import RuleSet


class RuleRepository:
    def __init__(self, path: Path) -> None:
        self._loader = RuleLoader(path)

    def get(self, category: str) -> tuple[RuleSet, str]:
        return self._loader.get(category)
