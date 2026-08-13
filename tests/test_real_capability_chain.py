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
        requested_capabilities=("data.validate",),
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

    result = outputs["validation_result"]

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

    result = outputs["validation_result"]

    assert result.category
    assert isinstance(result.issues, list)
    assert isinstance(result.clean, pd.DataFrame)
    assert isinstance(result.quarantine, pd.DataFrame)


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

    class SpyWorkflow:
        def run(
            self,
            frame,
            requested_category=None,
            execution_id=None,
        ):
            captured["validation_frame"] = frame
            captured["validation_requested_category"] = requested_category
            captured["validation_execution_id"] = execution_id

            return ValidationResult(
                category=requested_category or "unknown",
                clean=frame,
                quarantine=frame.iloc[0:0],
                issues=[],
                health_score=100.0,
                rule_version="test",
            )

    validation_capability = container.capabilities.get("data.validate")
    validation_capability._workflow = SpyWorkflow()

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

    result = outputs["validation_result"]

    assert captured["clean_input"] is original_frame
    assert captured["validation_frame"] is cleaned_frame

    assert captured["validation_frame"].equals(
        cleaned_frame
    )

    assert not captured["validation_frame"].equals(
        original_frame
    )

    assert result.clean is cleaned_frame