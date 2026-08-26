from database.models import make_session_factory
from repositories.workflow_executions import (
    WorkflowExecutionRepository,
)
from repositories.capability_execution_traces import (
    CapabilityExecutionTraceRepository,
)
from services.workflow_history_service import (
    WorkflowHistoryService,
)

def test_workflow_history_reads_workflow_execution():
    sessions = make_session_factory("sqlite://")

    executions = WorkflowExecutionRepository(sessions)
    traces = CapabilityExecutionTraceRepository(sessions)

    executions.create(
        execution_id="exec-1",
        workflow_id="wf-1",
        workflow_version="1.0",
        inputs={"file": "products.csv"},
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

    data = history.get_execution("exec-1")

    assert data["execution"].id == "exec-1"
    assert data["execution"].workflow_id == "wf-1"
    assert data["execution"].workflow_version == "1.0"
    assert len(data["traces"]) == 1

    trace = data["traces"][0]

    assert trace.capability_id == "data.validate"
    assert trace.capability_version == "1.0"
    assert trace.status == "COMPLETED"