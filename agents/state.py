"""Typed state shared by the LangGraph validation workflow."""
from __future__ import annotations

from typing import TypedDict

import pandas as pd

from domain.models import ValidationIssue, ValidationResult
from rule_engine.models import RuleSet


class WorkflowState(TypedDict, total=False):
    """Data passed between orchestration nodes, not a business-domain model."""

    frame: pd.DataFrame
    requested_category: str | None
    categories: list[str]
    plan: tuple[str, ...]
    category: str
    rules: RuleSet
    rule_version: str
    fixed_frame: pd.DataFrame
    issues: list[ValidationIssue]
    result: ValidationResult
