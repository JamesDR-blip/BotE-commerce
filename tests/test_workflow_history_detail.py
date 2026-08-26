from services.workflow_history_service import (
    WorkflowHistoryService,
)

from .conftest import (
    FakeExecutions,
    FakeTraces,
    FakeWorkflowExecutions,
)


def test_get_execution_detail():

    service = WorkflowHistoryService(
        executions=FakeExecutions(),
        traces=FakeTraces(),
    )

    result = service.get_execution_history(
        "exec-1"
    )

    assert result["execution"].id == "exec-1"
    assert len(result["traces"]) == 1

def test_get_workflow_execution_detail():
    service = WorkflowHistoryService(
        executions=FakeWorkflowExecutions(),
        traces=FakeTraces(),
    )

    result = service.get_workflow_execution_detail(
        "wf-exec-1"
    )

    assert result["execution_id"] == "wf-exec-1"
    assert result["workflow_id"] == "wf-1"
    assert result["workflow_version"] == "1.0"
    assert result["status"] == "COMPLETED"
    assert result["inputs"] == {
        "file": "products.csv",
    }
    assert result["outputs"] == {
        "file": "products.csv",
    }
    assert result["error"] is None
    assert len(result["traces"]) == 1

    trace = result["traces"][0]

    assert trace.capability_id == "data.clean"
    assert trace.capability_version == "1.0"
    assert trace.status == "COMPLETED"
    assert trace.started_at is None
    assert trace.finished_at is None