from services.workflow_history_service import (
    WorkflowHistoryService,
)
from .conftest import FakeExecutions, FakeTraces

def test_get_execution_history():

    service = WorkflowHistoryService(
        executions=FakeExecutions(),
        traces=FakeTraces(),
    )

    result = service.get_execution_history(
        "exec-1"
    )

    assert result["execution"].id == "exec-1"

    assert len(result["traces"]) == 1