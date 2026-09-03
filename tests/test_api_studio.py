from fastapi.testclient import TestClient

from api.main import create_app
from configs.settings import Settings
from domain.identity import CurrentUser
from api.dependencies import get_current_user


def build_client():
    app = create_app(
        Settings(
            database_url="sqlite://",
        )
    )

    app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="test-user")
    )

    return TestClient(app)


def test_create_workspace():
    client = build_client()

    response = client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo Workspace",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "ws-1"
    assert data["name"] == "Demo Workspace"
    assert "created_at" in data

def test_get_workspace():
    client = build_client()

    client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo Workspace",
        },
    )

    response = client.get(
        "/workspaces/ws-1"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "ws-1"
    assert data["name"] == "Demo Workspace"

def test_get_workspace_not_found():
    client = build_client()

    response = client.get(
        "/workspaces/missing"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Workspace not found: missing"
    )

def test_create_project():
    client = build_client()

    client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo Workspace",
        },
    )

    response = client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Catalog",
            "description": "Product catalog",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "p-1"
    assert data["workspace_id"] == "ws-1"
    assert data["name"] == "Catalog"
    assert data["description"] == "Product catalog"
    assert "created_at" in data

def test_get_project():
    client = build_client()

    client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo Workspace",
        },
    )

    client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Catalog",
        },
    )

    response = client.get("/projects/p-1")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "p-1"
    assert data["workspace_id"] == "ws-1"

def test_list_projects_by_workspace():
    client = build_client()

    client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo Workspace",
        },
    )

    client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Catalog",
        },
    )

    client.post(
        "/projects",
        json={
            "id": "p-2",
            "workspace_id": "ws-1",
            "name": "Orders",
        },
    )

    response = client.get(
        "/workspaces/ws-1/projects"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert {item["id"] for item in data} == {
        "p-1",
        "p-2",
    }

def test_get_project_not_found():
    client = build_client()

    response = client.get(
        "/projects/missing"
    )

    assert response.status_code == 404


def test_create_dataset():
    client = build_client()

    client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo Workspace",
        },
    )

    client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Catalog",
        },
    )

    response = client.post(
        "/datasets",
        json={
            "id": "d-1",
            "project_id": "p-1",
            "name": "catalog.csv",
            "source_type": "upload",
            "metadata": {
                "rows": 1000,
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "d-1"
    assert data["project_id"] == "p-1"
    assert data["name"] == "catalog.csv"
    assert data["source_type"] == "upload"
    assert data["metadata"]["rows"] == 1000
    assert "created_at" in data

def test_get_dataset():
    client = build_client()

    client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo Workspace",
        },
    )

    client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Catalog",
        },
    )

    client.post(
        "/datasets",
        json={
            "id": "d-1",
            "project_id": "p-1",
            "name": "catalog.csv",
            "source_type": "upload",
            "metadata": {},
        },
    )

    response = client.get("/datasets/d-1")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "d-1"
    assert data["project_id"] == "p-1"

def test_list_datasets_by_project():
    client = build_client()

    client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo Workspace",
        },
    )

    client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Catalog",
        },
    )

    for dataset_id in ("d-1", "d-2"):
        client.post(
            "/datasets",
            json={
                "id": dataset_id,
                "project_id": "p-1",
                "name": f"{dataset_id}.csv",
                "source_type": "upload",
                "metadata": {},
            },
        )

    response = client.get(
        "/projects/p-1/datasets"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert {item["id"] for item in data} == {
        "d-1",
        "d-2",
    }

def test_get_dataset_not_found():
    client = build_client()

    response = client.get(
        "/datasets/missing"
    )

    assert response.status_code == 404

def workflow_plan(version="1.0"):
    return {
        "version": version,
        "steps": [],
        "metadata": {},
    }
def test_create_workflow():
    client = build_client()

    client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo Workspace",
        },
    )

    client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Catalog",
        },
    )

    response = client.post(
        "/workflows",
        json={
            "id": "wf-1",
            "project_id": "p-1",
            "name": "Validation",
            "version": "1.0",
            "plan": workflow_plan(),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "wf-1"
    assert data["project_id"] == "p-1"
    assert data["name"] == "Validation"
    assert data["active_version"] == "1.0"
    assert data["status"] == "DRAFT"
    assert "created_at" in data

def test_get_workflow():
    client = build_client()

    client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo Workspace",
        },
    )

    client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Catalog",
        },
    )

    client.post(
        "/workflows",
        json={
            "id": "wf-1",
            "project_id": "p-1",
            "name": "Validation",
            "version": "1.0",
            "plan": workflow_plan(),
        },
    )

    response = client.get(
        "/workflows/wf-1"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "wf-1"
    assert data["active_version"] == "1.0"

def test_list_workflows_by_project():
    client = build_client()

    client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo Workspace",
        },
    )

    client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Catalog",
        },
    )

    for workflow_id in ("wf-1", "wf-2"):
        client.post(
            "/workflows",
            json={
                "id": workflow_id,
                "project_id": "p-1",
                "name": workflow_id,
                "version": "1.0",
                "plan": workflow_plan(),
            },
        )

    response = client.get(
        "/projects/p-1/workflows"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert {item["id"] for item in data} == {
        "wf-1",
        "wf-2",
    }

def test_workflow_version_lifecycle():
    client = build_client()

    client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo Workspace",
        },
    )

    client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Catalog",
        },
    )

    client.post(
        "/workflows",
        json={
            "id": "wf-1",
            "project_id": "p-1",
            "name": "Validation",
            "version": "1.0",
            "plan": workflow_plan("1.0"),
        },
    )

    response = client.post(
        "/workflows/wf-1/versions",
        json={
            "version": "2.0",
            "plan": {
                "version": "2.0",
                "steps": [],
                "metadata": {
                    "description": "Improved validation",
                },
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["workflow_id"] == "wf-1"
    assert data["version"] == "2.0"
    assert data["plan"]["version"] == "2.0"

def test_activate_workflow_version():
    client = build_client()

    client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Demo Workspace",
        },
    )

    client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Catalog",
        },
    )

    client.post(
        "/workflows",
        json={
            "id": "wf-1",
            "project_id": "p-1",
            "name": "Validation",
            "version": "1.0",
            "plan": workflow_plan("1.0"),
        },
    )

    client.post(
        "/workflows/wf-1/versions",
        json={
            "version": "2.0",
            "plan": workflow_plan("2.0"),
        },
    )

    response = client.post(
        "/workflows/wf-1/versions/2.0/activate"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "wf-1"
    assert data["active_version"] == "2.0"

def test_create_workspace_requires_authentication():
    client = TestClient(
        create_app(
            Settings(
                database_url="sqlite://",
            )
        )
    )

    response = client.post(
        "/workspaces",
        json={
            "id": "ws-unauth",
            "name": "Unauthenticated",
        },
    )

    assert response.status_code == 401