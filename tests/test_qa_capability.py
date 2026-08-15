from __future__ import annotations

import pandas as pd

from agents.qa import QAAgent
from capabilities.qa import (
    QA_CAPABILITY_SPEC,
    QACapability,
)
from domain.capabilities import CapabilityContext
from domain.models import ValidationIssue, ValidationResult


class FakeQAAgent:
    def __init__(self):
        self.calls = []

    def result(
        self,
        frame,
        issues,
        category,
        version,
    ):
        self.calls.append(
            {
                "frame": frame,
                "issues": issues,
                "category": category,
                "version": version,
            }
        )

        return ValidationResult(
            category=category,
            clean=frame,
            quarantine=frame.iloc[0:0],
            issues=issues,
            health_score=100.0,
            rule_version=version,
        )


def test_qa_capability_exposes_correct_spec():
    capability = QACapability(FakeQAAgent())

    assert capability.spec == QA_CAPABILITY_SPEC

    assert capability.spec.id == "data.qa"
    assert capability.spec.version == "1.0"

    assert capability.spec.input_keys == (
        "frame",
        "category",
        "issues",
        "rule_version",
    )

    assert capability.spec.output_keys == (
        "validation_result",
    )

    assert capability.spec.required_capabilities == (
        "data.validate",
    )


def test_qa_capability_delegates_to_agent():
    agent = FakeQAAgent()
    capability = QACapability(agent)

    frame = pd.DataFrame(
        {
            "product_title": [
                "Nike Air Max",
            ],
        }
    )

    issues = [
        ValidationIssue(
            row=2,
            field="color",
            code="missing",
            message="Missing color",
        )
    ]

    context = CapabilityContext(
        execution_id="qa-test-001",
        inputs={
            "frame": frame,
            "category": "Fashion",
            "issues": issues,
            "rule_version": "v1",
        },
    )

    result = capability.execute(context)

    validation_result = result.outputs[
        "validation_result"
    ]

    assert isinstance(
        validation_result,
        ValidationResult,
    )

    assert validation_result.category == "Fashion"
    assert validation_result.issues == issues
    assert validation_result.rule_version == "v1"

    assert len(agent.calls) == 1

    assert agent.calls[0]["frame"] is frame
    assert agent.calls[0]["issues"] == issues
    assert agent.calls[0]["category"] == "Fashion"
    assert agent.calls[0]["version"] == "v1"


def test_qa_capability_rejects_invalid_frame():
    capability = QACapability(FakeQAAgent())

    context = CapabilityContext(
        execution_id="qa-test-invalid-frame",
        inputs={
            "frame": "not-a-dataframe",
            "category": "Fashion",
            "issues": [],
            "rule_version": "v1",
        },
    )

    try:
        capability.execute(context)
    except TypeError as exc:
        assert "pandas DataFrame" in str(exc)
    else:
        raise AssertionError(
            "Expected TypeError"
        )