"""Extraction capability adapter."""

from __future__ import annotations

import pandas as pd

from agents.extraction import ExtractionAgent
from domain.capabilities import (
    CapabilityContext,
    CapabilityResult,
    CapabilitySpec,
)
from dataclasses import fields

from extractors.base import ExtractedAttributes

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
    parameter_keys=(
        "attributes",
    ),
    intents=(
        "extract_product_attributes",
        "extract_brand_model",
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

        requested_attributes = context.config.get("attributes")

        if requested_attributes is not None:
            allowed_attributes = {
                field.name
                for field in fields(ExtractedAttributes)
            }
            unknown_attributes = [
                attribute
                for attribute in requested_attributes
                if attribute not in allowed_attributes
            ]

            if unknown_attributes:
                raise ValueError(
                    "Unknown extraction attribute: "
                    + ", ".join(unknown_attributes)
                )

            extractions = [
                ExtractedAttributes(
                    **{
                        attribute: getattr(extraction, attribute)
                        if attribute in requested_attributes
                        else ""
                        for attribute in allowed_attributes
                    }
                )
                for extraction in extractions
            ]

        return CapabilityResult(
            outputs={
                "extractions": extractions,
            }
        )

__all__ = [
    "ExtractionCapability",
    "EXTRACTION_CAPABILITY_SPEC",
]