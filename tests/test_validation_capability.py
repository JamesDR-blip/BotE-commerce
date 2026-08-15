from __future__ import annotations

import pandas as pd

from capabilities.validation import ValidationCapability
from domain.capabilities import CapabilityContext
from domain.models import ValidationIssue
from rule_engine.models import RuleSet


class FakeRules:
    def __init__(self) -> None:
        self.calls = []

    def get(self, category: str):
        self.calls.append(category)

        return (
            RuleSet(category=category),
            "test-version",
        )


class FakeRuleRetriever:
    def __init__(self) -> None:
        self.calls = []

    def retrieve(self, category: str):
        self.calls.append(category)

        return (
            RuleSet(category=category),
            "test-version",
        )


class FakeValidator:
    def __init__(self) -> None:
        self.calls = []

    def validate(self, frame, validator, rules):
        self.calls.append(
            {
                "frame": frame,
                "validator": validator,
                "rules": rules,
            }
        )

        return [
            ValidationIssue(
                row=2,
                field="color",
                code="missing",
                message="Missing color",
            )
        ]


class FakeRegistry:
    def __init__(self) -> None:
        self.validator = object()
        self.calls = []

    def get(self, category: str):
        self.calls.append(category)
        return self.validator


def make_capability():
    rules = FakeRuleRetriever()
    validator = FakeValidator()
    registry = FakeRegistry()

    capability = ValidationCapability(
        rules=rules,
        validator=validator,
        registry=registry,
    )

    return capability, rules, validator, registry


def test_validation_capability_exposes_correct_spec():
    capability, _, _, _ = make_capability()

    assert capability.spec.id == "data.validate"
    assert capability.spec.version == "1.0"

    assert capability.spec.input_keys == (
        "frame",
        "category",
    )

    assert capability.spec.output_keys == (
        "frame",
        "category",
        "issues",
        "rule_version",
    )

    assert capability.spec.required_capabilities == (
        "data.clean",
    )


def test_validation_capability_executes_deterministic_validation():
    capability, rules, validator, registry = make_capability()

    frame = pd.DataFrame(
        {
            "product_title": ["Nike Air Max"],
        }
    )

    context = CapabilityContext(
        execution_id="execution-123",
        inputs={
            "frame": frame,
            "category": "Fashion",
        },
    )

    result = capability.execute(context)

    assert result.outputs["frame"] is frame
    assert result.outputs["category"] == "Fashion"
    assert result.outputs["rule_version"] == "test-version"

    assert len(result.outputs["issues"]) == 1
    assert result.outputs["issues"][0].code == "missing"

    assert rules.calls == ["Fashion"]
    assert registry.calls == ["Fashion"]

    assert len(validator.calls) == 1
    assert validator.calls[0]["frame"] is frame
    assert validator.calls[0]["rules"].category == "Fashion"


def test_validation_capability_requires_category():
    capability, _, _, _ = make_capability()

    frame = pd.DataFrame(
        {
            "product_title": ["Nike Air Max"],
        }
    )

    context = CapabilityContext(
        execution_id="execution-456",
        inputs={
            "frame": frame,
        },
    )

    try:
        capability.execute(context)
    except KeyError as exc:
        assert exc.args[0] == "category"
    else:
        raise AssertionError("Expected KeyError")


def test_validation_capability_rejects_invalid_frame():
    capability, _, _, _ = make_capability()

    context = CapabilityContext(
        execution_id="execution-789",
        inputs={
            "frame": ["not", "a", "dataframe"],
            "category": "Fashion",
        },
    )

    try:
        capability.execute(context)
    except TypeError as exc:
        assert "pandas DataFrame" in str(exc)
    else:
        raise AssertionError("Expected TypeError")