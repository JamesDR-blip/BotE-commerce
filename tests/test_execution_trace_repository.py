from datetime import datetime, timezone

from database.models import (
    ExecutionRecord,
    make_session_factory,
)

from repositories.execution_traces import (
    ExecutionTraceRepository,
)


def test_execution_trace_repository_persists_trace():
    sessions = make_session_factory("sqlite://")

    execution_repository = ExecutionTraceRepository(
        sessions
    )

    from repositories.executions import ExecutionRepository

    executions = ExecutionRepository(sessions)

    executions.create(
        ExecutionRecord(
            id="exec-1",
            category="Fashion",
            source_hash="a" * 64,
            rule_version="1.0",
            health_score=95.0,
            status="RUNNING",
        )
    )

    trace = execution_repository.create(
        execution_id="exec-1",
        capability_id="data.validate",
        capability_version="1.0",
        status="RUNNING",
        inputs={"frame": "products.csv"},
        started_at=datetime.now(timezone.utc),
    )

    execution_repository.complete(
        trace_id=trace.id,
        outputs={"result": "ok"},
        finished_at=datetime.now(timezone.utc),
    )

    records = execution_repository.list_by_execution(
        "exec-1"
    )

    assert len(records) == 1

    record = records[0]

    assert record.execution_id == "exec-1"
    assert record.capability_id == "data.validate"
    assert record.capability_version == "1.0"
    assert record.status == "COMPLETED"
    assert record.outputs_json == '{"result": "ok"}'