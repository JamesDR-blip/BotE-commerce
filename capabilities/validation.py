"""Validation capability adapter."""

from __future__ import annotations

import pandas as pd

from domain.capabilities import (
    CapabilityContext,
    CapabilityResult,
    CapabilitySpec,
)
from domain.validation_workflow import ValidationWorkflow


VALIDATION_CAPABILITY_SPEC = CapabilitySpec(
    id="data.validate",
    version="1.0",
    description="Validate ecommerce tabular data.",
    input_keys=(
        "frame",
        "requested_category",
    ),
    output_keys=(
        "validation_result",
    ),
)


class ValidationCapability:
    """Expose the existing validation workflow as a platform capability."""

    def __init__(self, workflow: ValidationWorkflow) -> None:
        self._workflow = workflow

    @property
    def spec(self) -> CapabilitySpec:
        return VALIDATION_CAPABILITY_SPEC

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        frame = context.inputs["frame"]
        requested_category = context.inputs.get("requested_category")

        if not isinstance(frame, pd.DataFrame):
            raise TypeError("data.validate requires a pandas DataFrame")

        result = self._workflow.run(
            frame=frame,
            requested_category=requested_category,
            execution_id=context.execution_id,
        )

        return CapabilityResult(
            outputs={
                "validation_result": result,
            }
        )


__all__ = [
    "ValidationCapability",
    "VALIDATION_CAPABILITY_SPEC",
]