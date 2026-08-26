from database.models import make_session_factory
from database.models import ExecutionRecord

from repositories.executions import ExecutionRepository
from repositories.execution_traces import (
    ExecutionTraceRepository,
)

from services.workflow_history_service import (
    WorkflowHistoryService,
)


def test_workflow_history_reads_persisted_execution_and_traces():
    sessions = make_session_factory("sqlite://")

    executions = ExecutionRepository(sessions)
    traces = ExecutionTraceRepository(sessions)

    executions.create(
        ExecutionRecord(
            id="exec-1",
            category="Fashion",
            source_hash="a" * 64,
            rule_version="1.0",
            health_score=95.0,
            status="COMPLETED",
        )
    )

    traces.create(
        execution_id="exec-1",
        capability_id="data.validate",
        capability_version="1.0",
        status="COMPLETED",
    )

    history = WorkflowHistoryService(
        executions=executions,
        traces=traces,
    )

    result = history.get_execution_history(
        "exec-1"
    )

    assert result["execution"].id == "exec-1"
    assert result["execution"].category == "Fashion"
    assert result["execution"].status == "COMPLETED"
    assert result["execution"].health_score == 95.0

    assert len(result["traces"]) == 1

    trace = result["traces"][0]

    assert trace.capability_id == "data.validate"
    assert trace.capability_version == "1.0"
    assert trace.status == "COMPLETED"