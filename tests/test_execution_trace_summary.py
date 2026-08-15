from datetime import datetime, UTC

from domain.execution_status import ExecutionStatus
from domain.execution_trace import (
    CapabilityExecutionRecord,
    ExecutionTrace,
)


def test_execution_trace_summary():

    now = datetime.now(UTC)

    trace = ExecutionTrace(
        execution_id="exec-1",
        records=(
            CapabilityExecutionRecord(
                capability_id="data.clean",
                capability_version="1.0",
                status=ExecutionStatus.COMPLETED,
                started_at=now,
                duration_ms=100,
            ),
            CapabilityExecutionRecord(
                capability_id="data.validate",
                capability_version="1.0",
                status=ExecutionStatus.FAILED,
                started_at=now,
                duration_ms=50,
                error="invalid",
            ),
        ),
    )

    summary = trace.summary()

    assert summary["execution_id"] == "exec-1"
    assert summary["total_steps"] == 2
    assert summary["completed"] == 1
    assert summary["failed"] == 1
    assert summary["duration_ms"] == 150