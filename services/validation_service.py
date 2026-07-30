"""Application service for concurrent category-validator execution."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from domain.models import ValidationIssue
from rule_engine.models import RuleSet
from validators.base import CategoryValidator


class ValidationService:
    """Run validator partitions using the existing four-way execution strategy."""

    def validate(self, frame: pd.DataFrame, validator: CategoryValidator, rules: RuleSet) -> list[ValidationIssue]:
        chunks = [chunk for chunk in (frame.iloc[index::4] for index in range(4)) if not chunk.empty]
        with ThreadPoolExecutor(max_workers=len(chunks)) as executor:
            return [issue for batch in executor.map(lambda chunk: validator.validate(chunk, rules), chunks) for issue in batch]


__all__ = ["ValidationService"]
