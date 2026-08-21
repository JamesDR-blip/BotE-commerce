from services.workflow_history_service import (
    WorkflowHistoryService,
)

from .conftest import (
    FakeExecutions,
    FakeTraces,
)


def test_get_execution_detail():

    service = WorkflowHistoryService(
        executions=FakeExecutions(),
        traces=FakeTraces(),
    )

    result = service.get_execution_detail(
        "exec-1"
    )

    assert result["execution_id"] == "exec-1"