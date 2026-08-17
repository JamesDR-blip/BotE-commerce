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
from services.execution_trace_collector import (
    ExecutionTraceCollector,
)

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

@dataclass
class ReplaceValueCapability:
    spec = CapabilitySpec(
        id="test.replace-value",
        version="1.0",
        description="Replaces an existing context value",
        input_keys=("value",),
        output_keys=("value",),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "value": f"{context.inputs['value']}-replaced",
            }
        )


@dataclass
class MissingDeclaredOutputCapability:
    spec = CapabilitySpec(
        id="test.missing-output",
        version="1.0",
        description="Returns only part of declared outputs",
        input_keys=("value",),
        output_keys=("result", "category"),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "result": context.inputs["value"],
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

    with pytest.raises(
        ValueError,
        match=r"(?i)version mismatch",
    ):
        executor.execute(
            plan,
            inputs={"value": "hello"},
            execution_id="version-mismatch-test",
        )


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


@dataclass
class RenamedCleanCapability:
    spec = CapabilitySpec(
        id="test.renamed-clean",
        version="1.0",
        description="Returns a renamed cleaned frame",
        input_keys=("frame",),
        output_keys=("cleaned_frame",),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "cleaned_frame": f"{context.inputs['frame']}-cleaned",
            }
        )


@dataclass
class FrameConsumerCapability:
    spec = CapabilitySpec(
        id="test.frame-consumer",
        version="1.0",
        description="Consumes a frame",
        input_keys=("frame",),
        output_keys=("result",),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "result": context.inputs["frame"],
            }
        )


def test_executor_does_not_implicitly_remap_renamed_output():
    registry = CapabilityRegistry()

    registry.register(RenamedCleanCapability())
    registry.register(FrameConsumerCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.renamed-clean",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.frame-consumer",
                capability_version="1.0",
            ),
        )
    )

    result = executor.execute(
        plan,
        inputs={"frame": "original"},
        execution_id="mapping-test",
    )

    assert result["cleaned_frame"] == "original-cleaned"

    # Current behavior: frame-consumer receives the original
    # frame because there is no explicit input mapping.
    assert result["result"] == "original"


def test_plan_step_supports_input_mapping():
    step = PlanStep(
        capability_id="test.frame-consumer",
        capability_version="1.0",
        input_mapping={
            "frame": "cleaned_frame",
        },
    )

    assert step.input_mapping == {
        "frame": "cleaned_frame",
    }


def test_executor_uses_explicit_input_mapping():
    registry = CapabilityRegistry()

    registry.register(RenamedCleanCapability())
    registry.register(FrameConsumerCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.renamed-clean",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.frame-consumer",
                capability_version="1.0",
                input_mapping={
                    "frame": "cleaned_frame",
                },
            ),
        )
    )

    result = executor.execute(
        plan,
        inputs={"frame": "original"},
        execution_id="mapping-test",
    )

    assert result["cleaned_frame"] == "original-cleaned"
    assert result["result"] == "original-cleaned"


def test_executor_rejects_missing_input_mapping_source():
    registry = CapabilityRegistry()

    registry.register(RenamedCleanCapability())
    registry.register(FrameConsumerCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.renamed-clean",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.frame-consumer",
                capability_version="1.0",
                input_mapping={
                    "frame": "does_not_exist",
                },
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)missing required input",
    ):
        executor.execute(
            plan,
            inputs={"frame": "original"},
            execution_id="mapping-test",
        )


def test_executor_uses_explicit_input_mapping_between_different_keys():
    registry = CapabilityRegistry()

    registry.register(RenamedCleanCapability())
    registry.register(FrameConsumerCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.renamed-clean",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.frame-consumer",
                capability_version="1.0",
                input_mapping={
                    "frame": "cleaned_frame",
                },
            ),
        )
    )

    result = executor.execute(
        plan,
        inputs={"frame": "original"},
        execution_id="mapping-test",
    )

    assert result["cleaned_frame"] == "original-cleaned"
    assert result["result"] == "original-cleaned"


def test_executor_rejects_input_mapping_with_missing_source():
    registry = CapabilityRegistry()

    registry.register(FrameConsumerCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.frame-consumer",
                capability_version="1.0",
                input_mapping={
                    "frame": "missing_frame",
                },
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)missing required input",
    ):
        executor.execute(
            plan,
            inputs={"frame": "original"},
            execution_id="mapping-test",
        )


def test_executor_does_not_implicitly_remap_between_different_keys():
    registry = CapabilityRegistry()

    registry.register(RenamedCleanCapability())
    registry.register(FrameConsumerCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.renamed-clean",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.frame-consumer",
                capability_version="1.0",
            ),
        )
    )

    result = executor.execute(
        plan,
        inputs={"frame": "original"},
        execution_id="mapping-test",
    )

    assert result["cleaned_frame"] == "original-cleaned"
    assert result["result"] == "original"



def test_executor_uses_explicit_input_mapping():
    registry = CapabilityRegistry()

    registry.register(RenamedCleanCapability())
    registry.register(FrameConsumerCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.renamed-clean",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.frame-consumer",
                capability_version="1.0",
                input_mapping={
                    "frame": "cleaned_frame",
                },
            ),
        )
    )

    result = executor.execute(
        plan,
        inputs={"frame": "original"},
        execution_id="mapping-test",
    )

    assert result["cleaned_frame"] == "original-cleaned"
    assert result["result"] == "original-cleaned"


def test_executor_rejects_unknown_parameter():
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
            inputs={"value": "SKU-001"},
            execution_id="parameter-test",
        )


def test_executor_allows_declared_output_to_replace_existing_context_value():
    registry = CapabilityRegistry()
    registry.register(ReplaceValueCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.replace-value",
                capability_version="1.0",
            ),
        )
    )

    result = executor.execute(
        plan,
        inputs={"value": "original"},
        execution_id="overwrite-test",
    )

    assert result["value"] == "original-replaced"


@dataclass
class NormalizeValueCapability:
    spec = CapabilitySpec(
        id="test.normalize-value",
        version="1.0",
        description="Normalizes a value",
        input_keys=("raw_value",),
        output_keys=("normalized_value",),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "normalized_value": context.inputs["raw_value"].strip().lower(),
            }
        )


@dataclass
class ExtractValueCapability:
    spec = CapabilitySpec(
        id="test.extract-value",
        version="1.0",
        description="Extracts a value",
        input_keys=("normalized_value",),
        output_keys=("extracted_value",),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "extracted_value": context.inputs["normalized_value"].upper(),
            }
        )


def test_executor_composes_multiple_explicit_input_mappings():
    registry = CapabilityRegistry()

    registry.register(NormalizeValueCapability())
    registry.register(ExtractValueCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.normalize-value",
                capability_version="1.0",
                input_mapping={
                    "raw_value": "value",
                },
            ),
            PlanStep(
                capability_id="test.extract-value",
                capability_version="1.0",
                input_mapping={
                    "normalized_value": "normalized_value",
                },
            ),
        )
    )

    result = executor.execute(
        plan,
        inputs={
            "value": "  nike  ",
        },
        execution_id="multi-step-mapping-test",
    )

    assert result["normalized_value"] == "nike"
    assert result["extracted_value"] == "NIKE"


def test_executor_rejects_missing_declared_output():
    registry = CapabilityRegistry()
    registry.register(MissingDeclaredOutputCapability())

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.missing-output",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)missing declared output",
    ):
        executor.execute(
            plan,
            inputs={"value": "hello"},
            execution_id="test-execution",
        )


def test_executor_records_actual_mapped_inputs_in_trace():
    registry = CapabilityRegistry()

    registry.register(RenamedCleanCapability())
    registry.register(FrameConsumerCapability())

    executor = CapabilityExecutor(registry)

    collector = ExecutionTraceCollector(
        execution_id="trace-mapping-test"
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.renamed-clean",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.frame-consumer",
                capability_version="1.0",
                input_mapping={
                    "frame": "cleaned_frame",
                },
            ),
        )
    )

    executor.execute(
        plan,
        inputs={
            "frame": "original",
        },
        execution_id="trace-mapping-test",
        trace_collector=collector,
    )

    trace = collector.trace()

    assert len(trace.records) == 2

    assert trace.records[0].inputs == {
        "frame": "original",
    }

    assert trace.records[1].inputs == {
        "frame": "original-cleaned",
    }


def test_executor_trace_captures_mapped_inputs():
    registry = CapabilityRegistry()

    registry.register(RenamedCleanCapability())
    registry.register(FrameConsumerCapability())

    executor = CapabilityExecutor(registry)

    collector = ExecutionTraceCollector(
        execution_id="trace-mapping-test",
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.renamed-clean",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.frame-consumer",
                capability_version="1.0",
                input_mapping={
                    "frame": "cleaned_frame",
                },
            ),
        )
    )

    result = executor.execute(
        plan,
        inputs={"frame": "original"},
        execution_id="trace-mapping-test",
        trace_collector=collector,
    )

    trace = collector.trace()

    assert len(trace.records) == 2

    clean_record = trace.records[0]
    consumer_record = trace.records[1]

    assert clean_record.inputs == {
        "frame": "original",
    }

    assert clean_record.outputs == {
        "cleaned_frame": "original-cleaned",
    }

    assert consumer_record.inputs == {
        "frame": "original-cleaned",
    }

    assert consumer_record.outputs == {
        "result": "original-cleaned",
    }

    assert result["result"] == "original-cleaned"