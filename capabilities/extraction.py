"""Extraction capability adapter."""

from __future__ import annotations

import pandas as pd

from agents.extraction import ExtractionAgent
from domain.capabilities import (
    CapabilityContext,
    CapabilityResult,
    CapabilitySpec,
)


EXTRACTION_CAPABILITY_SPEC = CapabilitySpec(
    id="data.extract",
    version="1.0",
    description="Extract structured product attributes from ecommerce tabular data.",
    input_keys=(
        "frame",
    ),
    output_keys=(
        "extractions",
    ),
)


class ExtractionCapability:
    """Expose the existing extraction agent as a platform capability."""

    def __init__(self, agent: ExtractionAgent) -> None:
        self._agent = agent

    @property
    def spec(self) -> CapabilitySpec:
        return EXTRACTION_CAPABILITY_SPEC

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        frame = context.inputs["frame"]

        if not isinstance(frame, pd.DataFrame):
            raise TypeError(
                "data.extract requires a pandas DataFrame"
            )

        extractions = self._agent.extract(frame)

        return CapabilityResult(
            outputs={
                "extractions": extractions,
            }
        )


__all__ = [
    "ExtractionCapability",
    "EXTRACTION_CAPABILITY_SPEC",
]