from domain.capability_registry import CapabilityRegistry
from domain.capabilities import (
    CapabilityContext,
    CapabilityResult,
    CapabilitySpec,
)
from domain.plans import (
    ExecutionPlan,
    PlanStep,
)
from services.capability_executor import CapabilityExecutor
from services.execution_trace_collector import (
    ExecutionTraceCollector,
)


class TraceEchoCapability:

    spec = CapabilitySpec(
        id="test.trace_echo",
        version="1.0",
        description="trace echo",
        input_keys=("value",),
        output_keys=("result",),
    )

    def execute(
        self,
        context: CapabilityContext,
    ):
        return CapabilityResult(
            outputs={
                "result": context.inputs["value"]
            }
        )


def test_executor_records_trace():

    registry = CapabilityRegistry()

    registry.register(
        TraceEchoCapability()
    )

    executor = CapabilityExecutor(
        registry
    )

    collector = ExecutionTraceCollector(
        execution_id="exec-1"
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.trace_echo",
            ),
        )
    )

    executor.execute(
        plan,
        inputs={
            "value": "hello"
        },
        execution_id="exec-1",
        trace_collector=collector,
    )

    trace = collector.trace()

    assert len(trace.records) == 1

    record = trace.records[0]

    assert record.capability_id == "test.trace_echo"
    assert record.status == "COMPLETED"