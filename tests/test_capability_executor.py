from dataclasses import dataclass

import pytest

from domain.capabilities import (
    CapabilityContext,
    CapabilityResult,
    CapabilitySpec,
)
from domain.capability_registry import CapabilityRegistry
from domain.plans import ExecutionPlan, PlanStep
from domain.exceptions import CapabilityNotFoundError
from services.capability_executor import CapabilityExecutor


@dataclass
class EchoCapability:
    spec = CapabilitySpec(
        id="test.echo",
        version="1.0",
        description="Echo input",
        input_keys=("value",),
        output_keys=("echo",),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "echo": context.inputs["value"],
            }
        )


def test_executor_executes_capability():
    registry = CapabilityRegistry()
    registry.register(EchoCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.echo",
                capability_version="1.0",
            ),
        )
    )

    result = executor.execute(
        plan,
        inputs={"value": "hello"},
        execution_id="test-execution",
    )

    assert result["echo"] == "hello"


@dataclass
class UpperCapability:
    spec = CapabilitySpec(
        id="test.upper",
        version="1.0",
        description="Uppercase input",
        input_keys=("echo",),
        output_keys=("upper",),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "upper": context.inputs["echo"].upper(),
            }
        )


def test_executor_passes_outputs_to_next_capability():
    registry = CapabilityRegistry()
    registry.register(EchoCapability())
    registry.register(UpperCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.echo",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.upper",
                capability_version="1.0",
            ),
        )
    )

    result = executor.execute(
        plan,
        inputs={"value": "hello"},
        execution_id="test-execution",
    )

    assert result["echo"] == "hello"
    assert result["upper"] == "HELLO"


def test_executor_rejects_capability_version_mismatch():
    registry = CapabilityRegistry()
    registry.register(EchoCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.echo",
                capability_version="2.0",
            ),
        )
    )

    try:
        executor.execute(
            plan,
            inputs={"value": "hello"},
            execution_id="test-execution",
        )
        assert False, "Expected version mismatch"
    except ValueError as exc:
        assert "version mismatch" in str(exc).lower()


def test_executor_rejects_unknown_capability():
    registry = CapabilityRegistry()
    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.unknown",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(CapabilityNotFoundError):
        executor.execute(
            plan,
            inputs={},
            execution_id="test-execution",
        )