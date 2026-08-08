"""Deterministic routing for the validation workflow."""
from __future__ import annotations

from typing import Literal

from .state import WorkflowState


ValidationRoute = Literal["validation"]


class WorkflowRouter:
    """Select a supported workflow path from the validated execution plan."""

    _VALIDATION_STEPS = (
        "requirements",
        "classify",
        "retrieve_rules",
        "extract",
        "autofix",
        "validate",
        "qa",
    )

    def route(self, state: WorkflowState) -> ValidationRoute:
        plan = state.get("plan", ())

        if plan == self._VALIDATION_STEPS:
            return "validation"

        raise ValueError(
            f"Unsupported workflow plan: {plan!r}"
        )


__all__ = ["WorkflowRouter", "ValidationRoute"]