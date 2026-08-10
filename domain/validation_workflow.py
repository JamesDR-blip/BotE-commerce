"""Application-level contract for validation workflow execution."""

from __future__ import annotations

from typing import Protocol

import pandas as pd

from domain.models import ValidationResult


class ValidationWorkflow(Protocol):
    """Contract exposed by the validation workflow to application consumers."""

    def run(
        self,
        frame: pd.DataFrame,
        requested_category: str | None = None,
        execution_id: str | None = None,
    ) -> ValidationResult:
        ...