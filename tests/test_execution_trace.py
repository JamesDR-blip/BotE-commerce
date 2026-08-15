from datetime import datetime, UTC

from domain.execution_trace import (
    CapabilityExecutionRecord,
    ExecutionTrace,
)
from domain.execution_status import ExecutionStatus


def test_capability_execution_record_contract():
    now = datetime.now(UTC)

    record = CapabilityExecutionRecord(
        capability_id="data.clean",
        capability_version="1.0",
        status="COMPLETED",
        started_at=now,
        finished_at=now,
        duration_ms=10.5,
    )

    assert record.capability_id == "data.clean"
    assert record.status == ExecutionStatus.COMPLETED
    assert record.duration_ms == 10.5


def test_execution_trace_contains_records():
    record = CapabilityExecutionRecord(
        capability_id="data.validate",
        capability_version="1.0",
        status="COMPLETED",
        started_at=datetime.now(UTC),
    )

    trace = ExecutionTrace(
        execution_id="exec-1",
        records=(record,),
    )

    assert trace.execution_id == "exec-1"
    assert len(trace.records) == 1


def test_execution_trace_is_immutable():
    trace = ExecutionTrace(
        execution_id="exec-1",
    )

    try:
        trace.execution_id = "changed"
    except AttributeError:
        pass
    else:
        raise AssertionError(
            "ExecutionTrace should be immutable"
        )