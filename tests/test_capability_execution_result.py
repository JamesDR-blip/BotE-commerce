from datetime import UTC, datetime

from domain.capability_execution import (
    CapabilityExecutionResult,
)
from domain.execution_status import ExecutionStatus
from domain.execution_trace import (
    CapabilityExecutionRecord,
    ExecutionTrace,
)
from domain.plans import ExecutionPlan, PlanStep


def test_capability_execution_result_contains_execution_contract():
    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="data.clean",
                capability_version="1.0",
            ),
        ),
        version="1.0",
        metadata={"source": "planner"},
    )

    trace = ExecutionTrace(
        execution_id="execution-1",
        records=(
            CapabilityExecutionRecord(
                capability_id="data.clean",
                capability_version="1.0",
                status=ExecutionStatus.COMPLETED,
                started_at=datetime.now(UTC),
                duration_ms=10.0,
            ),
        ),
    )

    result = CapabilityExecutionResult(
        outputs={"frame": "cleaned"},
        plan=plan,
        trace=trace,
        metadata={"planner_version": "planner-1"},
    )

    assert result.outputs == {"frame": "cleaned"}
    assert result.plan == plan
    assert result.trace == trace
    assert result.metadata == {
        "planner_version": "planner-1",
    }