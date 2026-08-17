from __future__ import annotations

import pandas as pd

from agents.requirement import ValidationRequirement
from configs.settings import Settings
from domain.models import ValidationResult
from services.container import Container


def test_real_validation_capability_chain():
    container = Container(Settings())

    requirement = ValidationRequirement(
        requested_category="Fashion",
        requested_capabilities=("data.qa",),
    )

    frame = pd.DataFrame(
        {
            "product_title": [
                "Nike Air Max 90",
                "Adidas Ultraboost",
            ],
        }
    )

    outputs = container.capability_execution.execute(
        requirement=requirement,
        inputs={
            "frame": frame,
            "requested_category": "Fashion",
        },
        execution_id="real-capability-chain-test",
    )

    result = outputs.outputs["validation_result"]

    assert isinstance(result, ValidationResult)
    assert result.category == "Fashion"
    assert isinstance(result.issues, list)
    assert result.clean is not None
    assert result.quarantine is not None


def test_real_capability_chain_clean_then_validate():
    container = Container(Settings())

    frame = pd.DataFrame(
        {
            "product_title": [
                "Nike Air Max 90",
                "Adidas Ultraboost",
            ],
        }
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.validate",),
    )

    plan = container.planner.plan(requirement)

    assert [
        step.capability_id
        for step in plan.steps
    ] == [
        "data.clean",
        "data.validate",
    ]

    outputs = container.capability_execution.execute(
        requirement=requirement,
        inputs={
            "frame": frame,
            "requested_category": None,
        },
        execution_id="real-chain-test",
    )

    assert "frame" in outputs.outputs
    assert "category" in outputs.outputs
    assert "issues" in outputs.outputs
    assert "rule_version" in outputs.outputs

    assert isinstance(outputs.outputs["frame"], pd.DataFrame)
    assert isinstance(outputs.outputs["category"], str)
    assert isinstance(outputs.outputs["issues"], list)
    assert isinstance(outputs.outputs["rule_version"], str)


def test_real_capability_chain_passes_cleaned_frame_to_validation():
    container = Container(Settings())

    original_frame = pd.DataFrame(
        {
            "product_title": [
                "Nike Air Max 90",
                "Adidas Ultraboost",
            ],
        }
    )

    cleaned_frame = original_frame.copy()
    cleaned_frame["cleaned_by_test"] = True

    captured = {}

    def fake_clean(frame, requested_category=None):
        captured["clean_input"] = frame
        captured["clean_requested_category"] = requested_category

        return "Fashion", cleaned_frame

    cleaning_capability = container.capabilities.get("data.clean")
    cleaning_capability._service.clean = fake_clean


    validation_capability = container.capabilities.get("data.validate")

    captured_validation = {}

    original_validate = validation_capability._validator.validate

    def spy_validate(frame, validator, rules):
        captured_validation["frame"] = frame
        captured_validation["validator"] = validator
        captured_validation["rules"] = rules

        return original_validate(frame, validator, rules)

    validation_capability._validator.validate = spy_validate

    requirement = ValidationRequirement(
        requested_capabilities=("data.validate",),
    )

    outputs = container.capability_execution.execute(
        requirement=requirement,
        inputs={
            "frame": original_frame,
            "requested_category": "Fashion",
        },
        execution_id="data-flow-test",
    )

    assert captured["clean_input"] is original_frame
    assert captured["clean_requested_category"] == "Fashion"

    assert list(
        captured_validation["frame"].columns
    ) == list(
        cleaned_frame.columns
    )

    assert outputs.outputs["frame"].equals(
        captured_validation["frame"]
    )
    assert outputs.outputs["category"] == "Fashion"
    assert isinstance(outputs.outputs["issues"], list)
    assert len(outputs.outputs["issues"]) >= 0
    assert isinstance(outputs.outputs["rule_version"], str)

def test_real_capability_chain_passes_extraction_parameters():
    container = Container(Settings())

    frame = pd.DataFrame(
        {
            "product_title": [
                "Nike AM-90",
            ],
        }
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.extract",),
        parameters={
            "data.extract": {
                "attributes": ("brand", "model"),
            },
        },
    )

    outputs = container.capability_execution.execute(
        requirement=requirement,
        inputs={
            "frame": frame,
        },
        execution_id="real-extraction-parameters-test",
    )

    extractions = outputs.outputs["extractions"]

    assert len(extractions) == 1

    extraction = extractions[0]

    assert extraction.brand == "Nike"
    assert extraction.model == "AM-90"
    assert extraction.color == ""