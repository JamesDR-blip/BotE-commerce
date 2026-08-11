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

@dataclass
class ConfigCapability:
    spec = CapabilitySpec(
        id="test.config",
        version="1.0",
        description="Reads invocation configuration",
        input_keys=("value",),
        output_keys=("result",),
        parameter_keys=("prefix",),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "result": (
                    f"{context.config['prefix']}"
                    f"{context.inputs['value']}"
                ),
            }
        )


@dataclass
class ExecutionIdCapability:
    spec = CapabilitySpec(
        id="test.execution-id",
        version="1.0",
        description="Reads execution ID",
        input_keys=(),
        output_keys=("execution_id",),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "execution_id": context.execution_id,
            }
        )


@dataclass
class ContextSeparationCapability:
    spec = CapabilitySpec(
        id="test.context-separation",
        version="1.0",
        description="Checks input/config separation",
        input_keys=("value",),
        output_keys=("result",),
        parameter_keys=("prefix",),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        assert context.inputs == {"value": "data"}
        assert context.config == {"prefix": "SKU-"}

        return CapabilityResult(
            outputs={
                "result": context.config["prefix"] + context.inputs["value"],
            }
        )
    

@dataclass
class FailingCapability:
    spec = CapabilitySpec(
        id="test.failing",
        version="1.0",
        description="Always fails",
        input_keys=(),
        output_keys=(),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        raise RuntimeError("capability execution failed")

@dataclass
class InvalidOutputCapability:
    spec = CapabilitySpec(
        id="test.invalid-output",
        version="1.0",
        description="Returns undeclared output",
        input_keys=("value",),
        output_keys=("result",),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "wrong_output": context.inputs["value"],
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


def test_executor_passes_step_parameters_to_capability_config():
    registry = CapabilityRegistry()
    registry.register(ConfigCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.config",
                capability_version="1.0",
                parameters={"prefix": "SKU-"},
            ),
        )
    )

    result = executor.execute(
        plan,
        inputs={"value": "123"},
        execution_id="test-execution",
    )

    assert result["result"] == "SKU-123"


def test_executor_passes_execution_id_to_capability():
    registry = CapabilityRegistry()
    registry.register(ExecutionIdCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.execution-id",
                capability_version="1.0",
            ),
        )
    )

    result = executor.execute(
        plan,
        inputs={},
        execution_id="execution-123",
    )

    assert result["execution_id"] == "execution-123"


def test_executor_keeps_inputs_and_parameters_separate():
    registry = CapabilityRegistry()
    registry.register(ContextSeparationCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.context-separation",
                capability_version="1.0",
                parameters={"prefix": "SKU-"},
            ),
        )
    )

    result = executor.execute(
        plan,
        inputs={"value": "data"},
        execution_id="test-execution",
    )

    assert result["result"] == "SKU-data"


def test_executor_propagates_capability_exception():
    registry = CapabilityRegistry()
    registry.register(FailingCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.failing",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(
        RuntimeError,
        match="capability execution failed",
    ):
        executor.execute(
            plan,
            inputs={},
            execution_id="test-execution",
        )


def test_executor_passes_step_parameters_to_capability():
    registry = CapabilityRegistry()
    registry.register(ConfigCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.config",
                capability_version="1.0",
                parameters={
                    "prefix": "validated-",
                },
            ),
        )
    )

    result = executor.execute(
        plan,
        inputs={"value": "product"},
        execution_id="test-execution",
    )

    assert result["result"] == "validated-product"


def test_executor_rejects_missing_required_input():
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

    with pytest.raises(ValueError, match=r"(?i)missing required input"):
        executor.execute(
            plan,
            inputs={},
            execution_id="test-execution",
        )

def test_executor_rejects_unknown_step_parameter():
    registry = CapabilityRegistry()
    registry.register(ConfigCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.config",
                capability_version="1.0",
                parameters={
                    "unknown": "value",
                },
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)unknown parameter",
    ):
        executor.execute(
            plan,
            inputs={"value": "123"},
            execution_id="test-execution",
        )


def test_executor_rejects_undeclared_output():
    registry = CapabilityRegistry()
    registry.register(InvalidOutputCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.invalid-output",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)undeclared output",
    ):
        executor.execute(
            plan,
            inputs={"value": "hello"},
            execution_id="test-execution",
        )