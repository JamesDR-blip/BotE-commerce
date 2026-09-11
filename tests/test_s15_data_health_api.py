from datetime import datetime, timezone

from fastapi.testclient import TestClient

from api.dependencies import get_current_user
from api.main import create_app
from configs.settings import Settings
from database.models import (
    DatasetRecord,
    ExecutionRecord,
    ProjectRecord,
    UserRecord,
    ValidationLogRecord,
    WorkspaceRecord,
)
from domain.identity import CurrentUser


def _client():
    return TestClient(
        create_app(
            Settings(database_url="sqlite://"),
        ),
        raise_server_exceptions=False,
    )


def _seed(client: TestClient) -> None:
    container = client.app.state.container

    with container.datasets._sessions() as session:
        session.add(
            UserRecord(
                id="user-1",
                email="owner@example.com",
            )
        )
        session.add(
            UserRecord(
                id="user-2",
                email="other@example.com",
            )
        )
        session.add(
            WorkspaceRecord(
                id="workspace-1",
                owner_id="user-1",
                name="Owner Workspace",
            )
        )
        session.add(
            WorkspaceRecord(
                id="workspace-2",
                owner_id="user-2",
                name="Other Workspace",
            )
        )
        session.add(
            ProjectRecord(
                id="project-1",
                workspace_id="workspace-1",
                name="Owner Project",
            )
        )
        session.add(
            ProjectRecord(
                id="project-2",
                workspace_id="workspace-2",
                name="Other Project",
            )
        )
        session.add(
            DatasetRecord(
                id="dataset-1",
                project_id="project-1",
                name="Products",
                source_type="upload",
                row_count=100,
                column_count=2,
                metadata_json={
                    "profile": {
                        "row_count": 100,
                        "column_count": 2,
                        "duplicate_row_count": 5,
                        "columns": [
                            {"name": "name", "null_ratio": 0.0},
                            {"name": "price", "null_ratio": 0.1},
                        ],
                    }
                },
                status="READY",
            )
        )
        session.add(
            DatasetRecord(
                id="dataset-2",
                project_id="project-2",
                name="Private Products",
                source_type="upload",
                row_count=100,
                column_count=1,
                metadata_json={
                    "profile": {
                        "row_count": 100,
                        "column_count": 1,
                        "duplicate_row_count": 0,
                        "columns": [
                            {"name": "name", "null_ratio": 0.0},
                        ],
                    }
                },
                status="READY",
            )
        )
        session.add(
            ExecutionRecord(
                id="execution-1",
                user_id="user-1",
                dataset_id="dataset-1",
                category="Fashion",
                source_hash="a" * 64,
                rule_version="1.0",
                health_score=85.0,
                status="COMPLETED",
                created_at=datetime.now(timezone.utc),
            )
        )
        session.add(
            ValidationLogRecord(
                execution_id="execution-1",
                row_number=17,
                field="price",
                code="invalid_price",
                message="Price must be positive.",
                severity="error",
            )
        )
        session.commit()


def test_health_metrics_requires_authentication(tmp_path):
    client = _client()

    response = client.get(
        "/health-metrics",
        params={"project_id": "project-1"},
    )

    assert response.status_code == 401


def test_health_metrics_returns_multidimensional_score(tmp_path):
    client = _client()
    _seed(client)

    client.app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="user-1")
    )

    response = client.get(
        "/health-metrics",
        params={"project_id": "project-1"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["project_id"] == "project-1"
    assert len(payload["items"]) == 1

    item = payload["items"][0]

    assert item["dataset_id"] == "dataset-1"
    assert item["dataset_name"] == "Products"
    assert item["aggregate"] > 0

    metrics = {
        metric["dimension"]: metric
        for metric in item["metrics"]
    }

    assert metrics["completeness"]["score"] == 95.0
    assert metrics["uniqueness"]["score"] == 95.0
    assert metrics["validity"]["score"] == 85.0
    assert metrics["timeliness"]["assessed"] is False


def test_health_metrics_respects_project_ownership(tmp_path):
    client = _client()
    _seed(client)

    client.app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="user-1")
    )

    response = client.get(
        "/health-metrics",
        params={"project_id": "project-2"},
    )

    assert response.status_code == 200
    assert response.json()["items"] == []


def test_diagnostics_are_sanitized(tmp_path):
    client = _client()
    _seed(client)

    client.app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="user-1")
    )

    response = client.get("/diagnostics/dataset-1")

    assert response.status_code == 200

    payload = response.json()

    assert payload["dataset_id"] == "dataset-1"
    assert len(payload["diagnostics"]) == 1

    diagnostic = payload["diagnostics"][0]

    assert diagnostic["code"] == "invalid_price"
    assert diagnostic["count"] == 1
    assert "row_number" not in diagnostic
    assert "17" not in diagnostic

    assert len(payload["remediation_proposals"]) == 1
    assert payload["remediation_proposals"][0]["status"] == "PROPOSED"


def test_diagnostics_do_not_cross_dataset_ownership(tmp_path):
    client = _client()
    _seed(client)

    client.app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="user-1")
    )

    response = client.get("/diagnostics/dataset-2")

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Dataset not found: dataset-2"
    )
