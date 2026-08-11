from __future__ import annotations

import pandas as pd

from capabilities.validation import ValidationCapability
from domain.capabilities import CapabilityContext
from domain.models import ValidationResult


class FakeValidationWorkflow:
    def __init__(self) -> None:
        self.calls = []

    def run(
        self,
        frame: pd.DataFrame,
        requested_category: str | None = None,
        execution_id: str | None = None,
    ) -> ValidationResult:
        self.calls.append(
            {
                "frame": frame,
                "requested_category": requested_category,
                "execution_id": execution_id,
            }
        )

        return ValidationResult(
            category=requested_category or "unknown",
            clean=frame,
            quarantine=frame.iloc[0:0],
            issues=[],
            health_score=1.0,
            rule_version="test",
        )


def test_validation_capability_exposes_correct_spec():
    workflow = FakeValidationWorkflow()
    capability = ValidationCapability(workflow)

    assert capability.spec.id == "data.validate"
    assert capability.spec.version == "1.0"
    assert capability.spec.input_keys == (
        "frame",
        "requested_category",
    )
    assert capability.spec.output_keys == (
        "validation_result",
    )
    assert capability.spec.required_capabilities == (
        "data.clean",
    )


def test_validation_capability_delegates_to_workflow():
    workflow = FakeValidationWorkflow()
    capability = ValidationCapability(workflow)

    frame = pd.DataFrame(
        {
            "product_title": ["Nike Air Max"],
        }
    )

    context = CapabilityContext(
        execution_id="execution-123",
        inputs={
            "frame": frame,
            "requested_category": "fashion",
        },
    )

    result = capability.execute(context)

    assert result.outputs["validation_result"].category == "fashion"

    assert len(workflow.calls) == 1
    assert workflow.calls[0]["frame"] is frame
    assert workflow.calls[0]["requested_category"] == "fashion"
    assert workflow.calls[0]["execution_id"] == "execution-123"


def test_validation_capability_allows_missing_requested_category():
    workflow = FakeValidationWorkflow()
    capability = ValidationCapability(workflow)

    frame = pd.DataFrame(
        {
            "product_title": ["Test Product"],
        }
    )

    context = CapabilityContext(
        execution_id="execution-456",
        inputs={
            "frame": frame,
        },
    )

    result = capability.execute(context)

    assert result.outputs["validation_result"].category == "unknown"


def test_validation_capability_rejects_invalid_frame():
    workflow = FakeValidationWorkflow()
    capability = ValidationCapability(workflow)

    context = CapabilityContext(
        execution_id="execution-789",
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