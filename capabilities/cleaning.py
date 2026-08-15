"""Cleaning capability adapter."""

from __future__ import annotations

import pandas as pd

from domain.capabilities import (
    CapabilityContext,
    CapabilityResult,
    CapabilitySpec,
)
from services.data_operations import DataOperationsService


CLEANING_CAPABILITY_SPEC = CapabilitySpec(
    id="data.clean",
    version="1.0",
    description="Clean ecommerce tabular data.",
    input_keys=(
        "frame",
        "requested_category",
    ),
    output_keys=(
        "frame",
        "category",
    ),
    intents=(
        "clean_product_data",
        "clean_product_titles",
    ),
)


class CleaningCapability:
    """Expose the existing cleaning service as a platform capability."""

    def __init__(self, service: DataOperationsService) -> None:
        self._service = service

    @property
    def spec(self) -> CapabilitySpec:
        return CLEANING_CAPABILITY_SPEC

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        frame = context.inputs["frame"]
        requested_category = context.inputs.get("requested_category")

        if not isinstance(frame, pd.DataFrame):
            raise TypeError("data.clean requires a pandas DataFrame")

        category, cleaned_frame = self._service.clean(
            frame=frame,
            requested_category=requested_category,
        )

        return CapabilityResult(
            outputs={
                "frame": cleaned_frame,
                "category": category,
            }
        )


__all__ = [
    "CleaningCapability",
    "CLEANING_CAPABILITY_SPEC",
]