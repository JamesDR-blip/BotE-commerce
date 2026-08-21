from datetime import datetime, timezone

from services.execution_trace_persistence import (
    ExecutionTracePersistence,
)


class FakeRepository:
    def __init__(self):
        self.created = []
        self.completed = []

    def create(
        self,
        *,
        execution_id,
        capability_id,
        capability_version,
        status,
        inputs,
        started_at,
    ):
        self.created.append(
            {
                "execution_id": execution_id,
                "capability_id": capability_id,
                "capability_version": capability_version,
                "status": status,
                "inputs": inputs,
                "started_at": started_at,
            }
        )

        return type(
            "Record",
            (),
            {"id": "trace-1"},
        )()

    def complete(
        self,
        *,
        trace_id,
        outputs,
        finished_at,
    ):
        self.completed.append(
            {
                "trace_id": trace_id,
                "outputs": outputs,
                "finished_at": finished_at,
            }
        )


class FakeTraceRecord:
    capability_id = "data.validate"
    capability_version = "1.0"
    status = type(
        "Status",
        (),
        {"value": "COMPLETED"},
    )()
    inputs = {"rows": 10}
    outputs = {"valid": True}
    started_at = datetime.now(timezone.utc)
    finished_at = datetime.now(timezone.utc)
    error = None


class FakeTrace:
    execution_id = "exec-1"
    records = (FakeTraceRecord(),)


def test_execution_trace_persistence_saves_completed_trace():
    repository = FakeRepository()

    persistence = ExecutionTracePersistence(
        repository
    )

    persistence.save(
        FakeTrace()
    )

    assert repository.created == [
        {
            "execution_id": "exec-1",
            "capability_id": "data.validate",
            "capability_version": "1.0",
            "status": "COMPLETED",
            "inputs": {"rows": 10},
            "started_at": FakeTraceRecord.started_at,
        }
    ]

    assert repository.completed[0]["trace_id"] == (
        "trace-1"
    )

    assert repository.completed[0]["outputs"] == {
        "valid": True
    }