from fastapi.testclient import TestClient

from api.main import create_app
from configs.settings import Settings


def _client() -> TestClient:
    return TestClient(
        create_app(
            Settings(database_url="sqlite://")
        ),
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