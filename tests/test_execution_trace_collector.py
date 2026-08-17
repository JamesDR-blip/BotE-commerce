from services.execution_trace_collector import (
    ExecutionTraceCollector,
)
from domain.execution_status import ExecutionStatus


def test_collector_tracks_completed_execution():

    collector = ExecutionTraceCollector(
        execution_id="exec-1"
    )

    index = collector.start(
        "data.clean",
        "1.0",
        inputs={
            "frame": "original",
        },
    )

    collector.complete(
        index,
        outputs={
            "cleaned": True,
        },
    )

    trace = collector.trace()

    assert trace.execution_id == "exec-1"

    record = trace.records[0]

    assert record.capability_id == "data.clean"
    assert record.status == ExecutionStatus.COMPLETED
    assert record.outputs["cleaned"] is True
    assert record.inputs == {
        "frame": "original",
    }


def test_collector_tracks_failed_execution():

    collector = ExecutionTraceCollector(
        execution_id="exec-2"
    )

    index = collector.start(
        "data.validate",
        "1.0",
        inputs={
            "frame": "original",
        },
    )

    collector.fail(
        index,
        ValueError("invalid data"),
    )

    record = collector.trace().records[0]

    assert record.status == ExecutionStatus.FAILED
    assert "invalid data" in record.error
    assert record.inputs == {
        "frame": "original",
    }