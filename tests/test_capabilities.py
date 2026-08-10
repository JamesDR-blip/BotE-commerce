from dataclasses import FrozenInstanceError

import pytest

from domain.capabilities import (
    CapabilityContext,
    CapabilityResult,
    CapabilitySpec,
)


def test_capability_spec_is_immutable():
    spec = CapabilitySpec(
        id="data.validate",
        version="1.0",
        description="Validate ecommerce data",
        input_keys=("frame",),
        output_keys=("validation_result",),
    )

    with pytest.raises(FrozenInstanceError):
        spec.id = "other"


def test_capability_context_contains_runtime_inputs():
    context = CapabilityContext(
        execution_id="exec-1",
        inputs={"frame": "test-frame"},
    )

    assert context.execution_id == "exec-1"
    assert context.inputs["frame"] == "test-frame"


def test_capability_context_has_optional_config_and_metadata():
    context = CapabilityContext(
        execution_id="exec-1",
        inputs={},
        config={"threshold": 0.8},
        metadata={"source": "test"},
    )

    assert context.config["threshold"] == 0.8
    assert context.metadata["source"] == "test"


def test_capability_result_contains_outputs():
    result = CapabilityResult(
        outputs={
            "validation_result": "result",
            "issues": [],
        },
    )

    assert result.outputs["validation_result"] == "result"
    assert result.outputs["issues"] == []


def test_capability_result_has_optional_metadata():
    result = CapabilityResult(
        outputs={},
        metadata={"duration_ms": 10},
    )

    assert result.metadata["duration_ms"] == 10


def test_object_can_implement_capability_protocol():
    class EchoCapability:
        spec = CapabilitySpec(
            id="test.echo",
            version="1.0",
            description="Echo a value",
            input_keys=("value",),
            output_keys=("value",),
        )

        def execute(self, context: CapabilityContext) -> CapabilityResult:
            return CapabilityResult(
                outputs={
                    "value": context.inputs["value"],
                },
            )

    capability = EchoCapability()

    context = CapabilityContext(
        execution_id="exec-1",
        inputs={"value": 42},
    )

    result = capability.execute(context)

    assert capability.spec.id == "test.echo"
    assert result.outputs["value"] == 42