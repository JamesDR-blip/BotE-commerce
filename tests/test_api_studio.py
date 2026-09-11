from fastapi.testclient import TestClient
from types import SimpleNamespace
from datetime import datetime, timezone

from api.main import create_app
from configs.settings import Settings
from domain.identity import CurrentUser
from api.dependencies import get_current_user, get_dataset_service



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

def test_get_project_forbidden_for_other_user():
    app = create_app(
        Settings(
            database_url="sqlite://",
        )
    )

    current_user = CurrentUser(user_id="owner-1")

    app.dependency_overrides[get_current_user] = (
        lambda: current_user
    )

    client = TestClient(app)

    client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Owner Workspace",
        },
    )

    client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Owner Project",
        },
    )

    current_user = CurrentUser(user_id="other-user")

    response = client.get("/projects/p-1")

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Project not found: p-1"
    )

def test_list_projects_forbidden_for_other_user():
    app = create_app(
        Settings(
            database_url="sqlite://",
        )
    )

    current_user = CurrentUser(user_id="owner-1")

    app.dependency_overrides[get_current_user] = (
        lambda: current_user
    )

    client = TestClient(app)

    client.post(
        "/workspaces",
        json={
            "id": "ws-1",
            "name": "Owner Workspace",
        },
    )

    client.post(
        "/projects",
        json={
            "id": "p-1",
            "workspace_id": "ws-1",
            "name": "Owner Project",
        },
    )

    current_user = CurrentUser(user_id="other-user")

    response = client.get(
        "/workspaces/ws-1/projects"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Workspace not found: ws-1"
    )

def test_user_cannot_get_other_users_dataset():
    owner_client = build_client()

    owner_client.post(
        "/workspaces",
        json={
            "id": "ws-owner",
            "name": "Owner Workspace",
        },
    )

    owner_client.post(
        "/projects",
        json={
            "id": "p-owner",
            "workspace_id": "ws-owner",
            "name": "Owner Project",
        },
    )

    owner_client.post(
        "/datasets",
        json={
            "id": "d-owner",
            "project_id": "p-owner",
            "name": "owner.csv",
            "source_type": "upload",
            "metadata": {},
        },
    )

    other_client = build_client()
    other_client.app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="other-user")
    )

    response = other_client.get(
        "/datasets/d-owner"
    )

    assert response.status_code == 404

def test_user_cannot_create_workflow_for_other_users_project():
    owner_client = build_client()

    owner_client.post(
        "/workspaces",
        json={
            "id": "ws-owner",
            "name": "Owner Workspace",
        },
    )

    owner_client.post(
        "/projects",
        json={
            "id": "p-owner",
            "workspace_id": "ws-owner",
            "name": "Owner Project",
        },
    )

    other_client = build_client()
    other_client.app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="other-user")
    )

    response = other_client.post(
        "/workflows",
        json={
            "id": "wf-forbidden",
            "project_id": "p-owner",
            "name": "Forbidden Workflow",
            "version": "1",
            "plan": {
                "steps": [],
                "version": "1.0",
                "metadata": {},
            },
        },
    )

    assert response.status_code == 404

def test_user_cannot_list_other_users_datasets():
    owner_client = build_client()

    owner_client.post(
        "/workspaces",
        json={
            "id": "ws-owner",
            "name": "Owner Workspace",
        },
    )

    owner_client.post(
        "/projects",
        json={
            "id": "p-owner",
            "workspace_id": "ws-owner",
            "name": "Owner Project",
        },
    )

    owner_client.post(
        "/datasets",
        json={
            "id": "d-owner",
            "project_id": "p-owner",
            "name": "owner.csv",
            "source_type": "upload",
            "metadata": {},
        },
    )

    other_client = build_client()
    other_client.app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="other-user")
    )

    response = other_client.get(
        "/projects/p-owner/datasets"
    )

    assert response.status_code == 200
    assert response.json() == []

def test_user_cannot_get_other_users_workflow():
    owner_client = build_client()

    owner_client.post(
        "/workspaces",
        json={
            "id": "ws-owner",
            "name": "Owner Workspace",
        },
    )

    owner_client.post(
        "/projects",
        json={
            "id": "p-owner",
            "workspace_id": "ws-owner",
            "name": "Owner Project",
        },
    )

    owner_client.post(
        "/workflows",
        json={
            "id": "wf-owner",
            "project_id": "p-owner",
            "name": "Owner Workflow",
            "version": "1",
            "plan": {
                "steps": [],
                "version": "1.0",
                "metadata": {},
            },
        },
    )

    other_client = build_client()
    other_client.app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="other-user")
    )

    response = other_client.get(
        "/workflows/wf-owner"
    )

    assert response.status_code == 404

def test_user_cannot_list_other_users_workflows():
    owner_client = build_client()

    owner_client.post(
        "/workspaces",
        json={
            "id": "ws-owner",
            "name": "Owner Workspace",
        },
    )

    owner_client.post(
        "/projects",
        json={
            "id": "p-owner",
            "workspace_id": "ws-owner",
            "name": "Owner Project",
        },
    )

    owner_client.post(
        "/workflows",
        json={
            "id": "wf-owner",
            "project_id": "p-owner",
            "name": "Owner Workflow",
            "version": "1",
            "plan": {
                "steps": [],
                "version": "1.0",
                "metadata": {},
            },
        },
    )

    response = owner_client.get(
        "/projects/p-owner/workflows"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1

    other_client = build_client()
    other_client.app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="other-user")
    )

    response = other_client.get(
        "/projects/p-owner/workflows"
    )

    assert response.status_code == 200
    assert response.json() == []

def test_upload_dataset():
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
        "/projects/p-1/datasets/upload",
        data={"name": "catalog.csv"},
        files={
            "file": (
                "catalog.csv",
                b"id,name,price\n1,Shirt,100\n2,Pants,200\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["project_id"] == "p-1"
    assert data["name"] == "catalog.csv"
    assert data["filename"] == "catalog.csv"
    assert data["file_format"] == "csv"
    assert data["row_count"] == 2
    assert data["column_count"] == 3
    assert data["status"] == "READY"

def test_upload_dataset_uses_streaming_ingestion():
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

    dataset_service = client.app.state.dataset_service
    captured = {}

    def fake_ingest_dataset_stream(**kwargs):
        captured.update(kwargs)

        return SimpleNamespace(
            id="d-1",
            project_id="p-1",
            name="catalog.csv",
            source_type="upload",
            filename="catalog.csv",
            file_format="csv",
            size_bytes=35,
            content_hash="abc123",
            row_count=2,
            column_count=3,
            status="READY",
            metadata={},
            created_at=datetime.now(timezone.utc),
        )

    dataset_service.ingest_dataset_stream = fake_ingest_dataset_stream

    content = b"id,name,price\n1,Shirt,100\n2,Pants,200\n"

    response = client.post(
        "/projects/p-1/datasets/upload",
        data={"name": "catalog.csv"},
        files={
            "file": (
                "catalog.csv",
                content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    assert captured["dataset_id"].startswith("dataset-")
    assert captured["project_id"] == "p-1"
    assert captured["name"] == "catalog.csv"
    assert captured["filename"] == "catalog.csv"
    assert captured["source_type"] == "upload"

    source = captured["source"]
    assert hasattr(source, "read")
    assert not isinstance(source, bytes)