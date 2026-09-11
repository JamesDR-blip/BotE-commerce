import json
import time
from fastapi.testclient import TestClient
from api.main import create_app
from configs.settings import Settings
from api.dependencies import get_current_user
from domain.identity import CurrentUser

class FailingWorkflowEngine:
    def execute(
        self,
        *,
        workflow_id,
        execution_id,
        inputs,
    ):
        from domain.studio.runtime import WorkflowExecution
        from domain.plans import ExecutionPlan

        runtime = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_version="1.0",
            plan=ExecutionPlan(
                steps=(),
                version="1.0",
                metadata={},
            ),
            inputs=inputs,
        )

        return runtime.start().fail(
            "capability execution failed"
        )

class SuccessfulCapabilityExecution:
    def execute_plan(
        self,
        *,
        plan,
        inputs,
        execution_id,
        trace_collector=None,
    ):
        if trace_collector is not None:
            index = trace_collector.start(
                "data.validate",
                "1.0",
                inputs={
                    "frame": "test-frame",
                    "category": "Fashion",
                },
            )

            trace_collector.complete(
                index,
                {
                    "frame": "test-frame",
                    "category": "Fashion",
                    "issues": [],
                    "rule_version": "test",
                },
            )

        return type(
            "Result",
            (),
            {
                "outputs": {
                    "frame": "test-frame",
                    "category": "Fashion",
                    "issues": [],
                    "rule_version": "test",
                },
            },
        )()


def _client() -> TestClient:
    app = create_app(
        Settings(database_url="sqlite://")
    )

    app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="test-user")
    )

    return TestClient(
        app,
        raise_server_exceptions=False,
    )


def test_workflow_execution_endpoint_runs_workflow() -> None:
    client = _client()

    workspace_response = client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo",
        },
    )

    assert workspace_response.status_code == 200

    project_response = client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Catalog",
            "description": "Runtime test",
        },
    )

    assert project_response.status_code == 200

    workflow_response = client.post(
        "/workflows",
        json={
            "id": "wf-1",
            "project_id": "p-1",
            "name": "Validation",
            "version": "1.0",
            "plan": {
                "version": "1.0",
                "steps": [],
                "metadata": {},
            },
        },
    )

    assert workflow_response.status_code == 200

    response = client.post(
        "/workflows/wf-1/execute",
        json={
            "inputs": {
                "file": "products.csv",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["execution_id"]
    assert payload["workflow_id"] == "wf-1"
    assert payload["workflow_version"] == "1.0"
    assert payload["status"] == "COMPLETED"
    assert payload["success"] is True
    assert payload["outputs"] == {
        "file": "products.csv",
    }
    assert payload["error"] is None
    assert payload["started_at"]
    assert payload["finished_at"]

    execution = (
        client.app.state.container
        .workflow_executions
        .get(payload["execution_id"])
    )

    assert execution is not None
    assert execution.workflow_id == "wf-1"
    assert execution.workflow_version == "1.0"
    assert execution.status == "COMPLETED"

    assert json.loads(execution.inputs_json) == {
        "file": "products.csv",
    }

    assert json.loads(execution.outputs_json) == {
        "file": "products.csv",
    }

    assert execution.started_at is not None
    assert execution.finished_at is not None
    assert execution.finished_at >= execution.started_at

def test_workflow_execution_endpoint_persists_failed_runtime() -> None:
    client = _client()

    workspace_response = client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo",
        },
    )

    assert workspace_response.status_code == 200

    project_response = client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Catalog",
            "description": "Failure persistence test",
        },
    )

    assert project_response.status_code == 200

    workflow_response = client.post(
        "/workflows",
        json={
            "id": "wf-1",
            "project_id": "p-1",
            "name": "Validation",
            "version": "1.0",
            "plan": {
                "version": "1.0",
                "steps": [],
                "metadata": {},
            },
        },
    )

    assert workflow_response.status_code == 200

    class FailingCapabilityExecution:
        def execute_plan(self, **kwargs):
            raise RuntimeError(
                "capability execution failed"
            )

    client.app.state.container.workflow_engine.capability_execution = (
        FailingCapabilityExecution()
    )

    response = client.post(
        "/workflows/wf-1/execute",
        json={
            "inputs": {
                "file": "products.csv",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["execution_id"]
    assert payload["workflow_id"] == "wf-1"
    assert payload["workflow_version"] == "1.0"
    assert payload["status"] == "FAILED"
    assert payload["success"] is False
    assert payload["outputs"] == {}
    assert payload["error"] == (
        "capability execution failed"
    )
    assert payload["started_at"]
    assert payload["finished_at"]

    execution = (
        client.app.state.container
        .workflow_executions
        .get(payload["execution_id"])
    )

    assert execution is not None
    assert execution.workflow_id == "wf-1"
    assert execution.workflow_version == "1.0"
    assert execution.status == "FAILED"
    assert execution.error == (
        "capability execution failed"
    )
    assert execution.started_at is not None
    assert execution.finished_at is not None
    assert execution.finished_at >= execution.started_at

def test_workflow_execution_endpoint_returns_failed_runtime():
    client = _client()

    workspace_response = client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo",
        },
    )

    assert workspace_response.status_code == 200

    project_response = client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Catalog",
            "description": "Failure test",
        },
    )

    assert project_response.status_code == 200

    workflow_response = client.post(
        "/workflows",
        json={
            "id": "wf-1",
            "project_id": "p-1",
            "name": "Validation",
            "version": "1.0",
            "plan": {
                "version": "1.0",
                "steps": [],
                "metadata": {},
            },
        },
    )

    assert workflow_response.status_code == 200

    client.app.state.container.workflow_engine = (
        FailingWorkflowEngine()
    )

    response = client.post(
        "/workflows/wf-1/execute",
        json={
            "inputs": {
                "file": "products.csv",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["execution_id"]
    assert payload["workflow_id"] == "wf-1"
    assert payload["workflow_version"] == "1.0"
    assert payload["status"] == "FAILED"
    assert payload["success"] is False
    assert payload["outputs"] == {}
    assert payload["error"] == (
        "capability execution failed"
    )
    assert payload["started_at"]
    assert payload["finished_at"]


def test_workflow_execution_persists_capability_traces() -> None:
    client = _client()

    fake_capability_execution = SuccessfulCapabilityExecution()

    client.app.state.container.capability_execution = (
        fake_capability_execution
    )
    client.app.state.container.workflow_engine.capability_execution = (
        fake_capability_execution
    )

    workspace_response = client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo",
        },
    )

    assert workspace_response.status_code == 200

    project_response = client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Catalog",
            "description": "Trace persistence test",
        },
    )

    assert project_response.status_code == 200

    workflow_response = client.post(
        "/workflows",
        json={
            "id": "wf-1",
            "project_id": "p-1",
            "name": "Validation",
            "version": "1.0",
            "plan": {
                "version": "1.0",
                "steps": [
                    {
                        "capability_id": "data.validate",
                        "capability_version": "1.0",
                        "input_mapping": {},
                        "parameters": {},
                    }
                ],
                "metadata": {},
            },
        },
    )

    assert workflow_response.status_code == 200

    response = client.post(
        "/workflows/wf-1/execute",
        json={
            "inputs": {
                "file": "products.csv",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    execution_id = payload["execution_id"]
    

    traces = (
        client.app.state.container
        .workflow_capability_traces
        .list_by_execution(execution_id)
    )

    assert len(traces) == 1

    trace = traces[0]

    assert trace.execution_id == execution_id
    assert trace.capability_id == "data.validate"
    assert trace.capability_version == "1.0"
    assert trace.status == "COMPLETED"
    assert trace.started_at is not None
    assert trace.finished_at is not None

def test_workflow_execution_detail_reads_persisted_workflow_execution():
    client = _client()

    workspace_response = client.post(
        "/workspaces",
        json={
            "id": "ws-detail",
            "name": "Detail Test",
        },
    )
    assert workspace_response.status_code == 200

    project_response = client.post(
        "/projects",
        json={
            "id": "p-detail",
            "workspace_id": "ws-detail",
            "name": "Catalog",
            "description": "Workflow detail test",
        },
    )
    assert project_response.status_code == 200

    workflow_response = client.post(
        "/workflows",
        json={
            "id": "wf-detail",
            "project_id": "p-detail",
            "name": "Validation",
            "version": "1.0",
            "plan": {
                "version": "1.0",
                "steps": [],
                "metadata": {},
            },
        },
    )
    assert workflow_response.status_code == 200

    execute_response = client.post(
        "/workflows/wf-detail/execute",
        json={
            "inputs": {
                "file": "products.csv",
            },
        },
    )

    assert execute_response.status_code == 200

    execution_id = execute_response.json()["execution_id"]

    client.app.state.container.workflow_capability_traces.create(
        execution_id=execution_id,
        capability_id="data.validate",
        capability_version="1.0",
        status="COMPLETED",
    )

    detail_response = client.get(
        f"/workflow-executions/{execution_id}"
    )

    assert detail_response.status_code == 200

    payload = detail_response.json()

    assert payload["workflow_id"] == "wf-detail"
    assert payload["workflow_version"] == "1.0"
    assert payload["status"] == "COMPLETED"

    assert len(payload["traces"]) == 1

    trace = payload["traces"][0]

    assert trace["capability_id"] == "data.validate"
    assert trace["capability_version"] == "1.0"
    assert trace["status"] == "COMPLETED"
    assert trace["started_at"] is None
    assert trace["finished_at"] is None

def test_workflow_execution_detail_returns_404_for_missing_execution():
    client = _client()

    response = client.get(
        "/workflow-executions/missing-workflow-execution"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Workflow execution not found: "
        "missing-workflow-execution"
    )
def test_workflow_async_execution_endpoint_returns_execution_id() -> None:
    client = _client()

    workspace_response = client.post(
        "/workspaces",
        json={
            "id": "ws-async",
            "name": "Async Demo",
        },
    )
    assert workspace_response.status_code == 200

    project_response = client.post(
        "/projects",
        json={
            "id": "p-async",
            "workspace_id": "ws-async",
            "name": "Async Catalog",
            "description": "Async workflow test",
        },
    )
    assert project_response.status_code == 200

    workflow_response = client.post(
        "/workflows",
        json={
            "id": "wf-async",
            "project_id": "p-async",
            "name": "Async Validation",
            "version": "1.0",
            "plan": {
                "version": "1.0",
                "steps": [],
                "metadata": {},
            },
        },
    )
    assert workflow_response.status_code == 200

    response = client.post(
        "/workflows/wf-async/execute-async",
        json={
            "inputs": {
                "file": "products.csv",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["execution_id"]
    assert payload["workflow_id"] == "wf-async"
    assert payload["workflow_version"] == "1.0"
    assert payload["status"] in {
        "QUEUED",
        "RUNNING",
        "COMPLETED",
    }
    assert payload["outputs"] in ({}, {"file": "products.csv"})

    execution = (
        client.app.state.container
        .workflow_executions
        .get(payload["execution_id"])
    )

    assert execution is not None
    assert execution.workflow_id == "wf-async"
    assert execution.workflow_version == "1.0"


def test_workflow_async_status_endpoint_reads_persisted_execution() -> None:
    client = _client()

    workspace_response = client.post(
        "/workspaces",
        json={
            "id": "ws-status",
            "name": "Async Status Demo",
        },
    )
    assert workspace_response.status_code == 200

    project_response = client.post(
        "/projects",
        json={
            "id": "p-status",
            "workspace_id": "ws-status",
            "name": "Async Status Catalog",
            "description": "Async status test",
        },
    )
    assert project_response.status_code == 200

    workflow_response = client.post(
        "/workflows",
        json={
            "id": "wf-status",
            "project_id": "p-status",
            "name": "Async Status Validation",
            "version": "1.0",
            "plan": {
                "version": "1.0",
                "steps": [],
                "metadata": {},
            },
        },
    )
    assert workflow_response.status_code == 200

    execute_response = client.post(
        "/workflows/wf-status/execute-async",
        json={
            "inputs": {
                "file": "products.csv",
            },
        },
    )

    assert execute_response.status_code == 200

    execution_id = execute_response.json()["execution_id"]

    terminal_statuses = {"COMPLETED", "FAILED"}
    status_payload = None

    for _ in range(40):
        status_response = client.get(
            f"/workflow-executions/{execution_id}/status"
        )

        assert status_response.status_code == 200

        status_payload = status_response.json()

        if status_payload["status"] in terminal_statuses:
            break

        time.sleep(0.025)

    assert status_payload is not None
    assert status_payload["execution_id"] == execution_id
    assert status_payload["workflow_id"] == "wf-status"
    assert status_payload["workflow_version"] == "1.0"
    assert status_payload["status"] in terminal_statuses
    assert status_payload["success"] is (
        status_payload["status"] == "COMPLETED"
    )

    execution = (
        client.app.state.container
        .workflow_executions
        .get(execution_id)
    )

    assert execution is not None
    assert execution.status == status_payload["status"]


def test_workflow_async_status_returns_404_for_missing_execution() -> None:
    client = _client()

    response = client.get(
        "/workflow-executions/missing-async-execution/status"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Workflow execution not found: "
        "missing-async-execution"
    )
