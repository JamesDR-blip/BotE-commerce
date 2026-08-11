from __future__ import annotations

import pandas as pd

from capabilities.extraction import (
    ExtractionCapability,
)
from domain.capabilities import CapabilityContext


class FakeExtractionAgent:
    def __init__(self) -> None:
        self.calls = []

    def extract(self, frame: pd.DataFrame):
        self.calls.append(frame)
        return [
            {
                "brand": "Nike",
                "model": "Air Max",
            }
        ]


def test_extraction_capability_exposes_correct_spec():
    agent = FakeExtractionAgent()
    capability = ExtractionCapability(agent)

    assert capability.spec.id == "data.extract"
    assert capability.spec.version == "1.0"
    assert capability.spec.input_keys == (
        "frame",
    )
    assert capability.spec.output_keys == (
        "extractions",
    )


def test_extraction_capability_delegates_to_agent():
    agent = FakeExtractionAgent()
    capability = ExtractionCapability(agent)

    frame = pd.DataFrame(
        {
            "product_title": ["Nike Air Max"],
        }
    )

    context = CapabilityContext(
        execution_id="execution-123",
        inputs={
            "frame": frame,
        },
    )

    result = capability.execute(context)

    assert result.outputs["extractions"] == [
        {
            "brand": "Nike",
            "model": "Air Max",
        }
    ]

    assert len(agent.calls) == 1
    assert agent.calls[0] is frame


def test_extraction_capability_rejects_invalid_frame():
    agent = FakeExtractionAgent()
    capability = ExtractionCapability(agent)

    context = CapabilityContext(
        execution_id="execution-456",
        inputs={
            "frame": ["not", "a", "dataframe"],
        },
    )

    try:
        capability.execute(context)
    except TypeError as exc:
        assert "pandas DataFrame" in str(exc)
    else:
        raise AssertionError("Expected TypeError")