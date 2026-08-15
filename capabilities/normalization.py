"""Normalization capability adapter."""

from __future__ import annotations

import pandas as pd

from domain.capabilities import (
    CapabilityContext,
    CapabilityResult,
    CapabilitySpec,
)
from services.normalization_service import NormalizationService


NORMALIZATION_CAPABILITY_SPEC = CapabilitySpec(
    id="data.normalize",
    version="1.0",
    description="Normalize ecommerce tabular data fields.",
    input_keys=(
        "frame",
    ),
    output_keys=(
        "frame",
    ),
    parameter_keys=(
        "fields",
    ),
)


class NormalizationCapability:
    """Expose the normalization service as a platform capability."""

    def __init__(self, service: NormalizationService) -> None:
        self._service = service

    @property
    def spec(self) -> CapabilitySpec:
        return NORMALIZATION_CAPABILITY_SPEC

    def execute(
        self,
        context: CapabilityContext,
    ) -> CapabilityResult:
        frame = context.inputs["frame"]

        if not isinstance(frame, pd.DataFrame):
            raise TypeError(
                "data.normalize requires a pandas DataFrame"
            )

        fields = context.config.get("fields")

        normalized_frame = self._service.normalize(
            frame=frame,
            fields=fields,
        )

        return CapabilityResult(
            outputs={
                "frame": normalized_frame,
            }
        )


__all__ = [
    "NormalizationCapability",
    "NORMALIZATION_CAPABILITY_SPEC",
]
