from services.workflow_runtime_service import WorkflowRuntimeService


class FakeEngine:
    def __init__(self) -> None:
        self.calls = []

    def execute(self, **kwargs):
        self.calls.append(kwargs)
        return "runtime"


class FakeHistory:
    def get_workflow_execution_detail(self, execution_id):
        return {"execution_id": execution_id}


def test_runtime_service_delegates_execution_with_a_generated_id():
    engine = FakeEngine()
    service = WorkflowRuntimeService(
        workflow_engine=lambda: engine,
        workflow_history=FakeHistory,
    )

    result = service.execute(
        workflow_id="workflow-1",
        inputs={"source": "catalog"},
    )

    assert result == "runtime"
    assert engine.calls[0]["workflow_id"] == "workflow-1"
    assert engine.calls[0]["inputs"] == {"source": "catalog"}
    assert engine.calls[0]["execution_id"]


def test_runtime_service_delegates_history_lookup():
    service = WorkflowRuntimeService(
        workflow_engine=FakeEngine,
        workflow_history=FakeHistory,
    )

    assert service.get_execution_detail("execution-1") == {
        "execution_id": "execution-1"
    }
