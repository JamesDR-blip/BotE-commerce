"""Validator plugin protocol."""
from __future__ import annotations
from abc import ABC, abstractmethod
import pandas as pd
from domain.models import ValidationIssue


class CategoryValidator(ABC):
    """A pure plugin: validate and safe, deterministic normalisation only."""
    category: str

    @abstractmethod
    def validate(self, frame: pd.DataFrame, rules: dict) -> list[ValidationIssue]: ...

    def autofix(self, frame: pd.DataFrame) -> pd.DataFrame:
        return frame.copy()


__all__ = ["CategoryValidator"]
