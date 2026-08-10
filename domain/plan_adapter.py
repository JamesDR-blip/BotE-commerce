"""Adapters between legacy workflow plans and capability execution plans."""

from __future__ import annotations

from domain.plans import ExecutionPlan, PlanStep


VALIDATION_CAPABILITY_ID = "data.validate"


def validation_execution_plan() -> ExecutionPlan:
    """Represent the existing validation workflow as one capability."""
    return ExecutionPlan(
        steps=(
            PlanStep(
                capability_id=VALIDATION_CAPABILITY_ID,
            ),
        ),
        metadata={
            "source": "legacy-validation-workflow",
        },
    )


__all__ = [
    "VALIDATION_CAPABILITY_ID",
    "validation_execution_plan",
]