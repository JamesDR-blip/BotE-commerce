from __future__ import annotations

import pandas as pd
import pytest

from capabilities.normalization import NormalizationCapability
from domain.capabilities import CapabilityContext
from services.normalization_service import NormalizationService


def test_normalization_capability_normalizes_requested_fields():
    frame = pd.DataFrame(
        {
            "product_title": ["  Nike   Air   Max  "],
            "color": [" black "],
            "sku": ["AbC-001"],
        }
    )

    capability = NormalizationCapability(
        NormalizationService()
    )

    result = capability.execute(
        CapabilityContext(
            execution_id="normalization-test-001",
            inputs={
                "frame": frame,
            },
            config={
                "fields": (
                    "product_title",
                    "color",
                ),
            },
        )
    )

    normalized = result.outputs["frame"]

    assert normalized["product_title"].tolist() == [
        "Nike Air Max"
    ]

    assert normalized["color"].tolist() == [
        "Black"
    ]

    assert normalized["sku"].tolist() == [
        "AbC-001"
    ]

    assert frame["product_title"].tolist() == [
        "  Nike   Air   Max  "
    ]

    assert frame["color"].tolist() == [
        " black "
    ]


def test_normalization_capability_declares_correct_contract():
    capability = NormalizationCapability(
        NormalizationService()
    )

    assert capability.spec.id == "data.normalize"
    assert capability.spec.version == "1.0"

    assert capability.spec.input_keys == (
        "frame",
    )

    assert capability.spec.output_keys == (
        "frame",
    )

    assert capability.spec.parameter_keys == (
        "fields",
    )


def test_normalization_capability_rejects_non_dataframe():
    capability = NormalizationCapability(
        NormalizationService()
    )

    with pytest.raises(
        TypeError,
        match="data.normalize requires a pandas DataFrame",
    ):
        capability.execute(
            CapabilityContext(
                execution_id="normalization-test-002",
                inputs={
                    "frame": ["not", "a", "dataframe"],
                },
            )
        )