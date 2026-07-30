"""Validator plugin protocol."""
from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Mapping
import pandas as pd
from domain.models import ValidationIssue
from rule_engine.models import RuleSet


class CategoryValidator(ABC):
    """A pure plugin: validate and safe, deterministic normalisation only."""
    category: str

    @abstractmethod
    def validate(self, frame: pd.DataFrame, rules: RuleSet | Mapping[str, object]) -> list[ValidationIssue]: ...

    def autofix(self, frame: pd.DataFrame) -> pd.DataFrame:
        return frame.copy()


__all__ = ["CategoryValidator"]
