from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from api.dependencies import (
    get_audit_service,
    get_current_user,
    get_dataset_service,
    get_lineage_tracking_service,
)
from api.main import create_app
from configs.settings import Settings
from domain.identity import CurrentUser


def _client():
    app = create_app(Settings(database_url="sqlite://"))
    app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="owner-1")
    )
    return app, TestClient(app)


def _dataset(dataset_id="dataset-1"):
    return SimpleNamespace(
        id=dataset_id,
        project_id="project-1",
        name="products",
        source_type="upload",
        created_at=datetime(
            2026,
            9,
            14,
            tzinfo=timezone.utc,
        ),
    )


def _lineage_event():
    return SimpleNamespace(
        id="lineage-1",
        dataset_id="dataset-1",
        execution_id="execution-1",
        workflow_id="workflow-1",
        workflow_version="1.0",
        capability_id="data.clean",
        capability_version="1.0",
        event_type="CAPABILITY_EXECUTED",
        input_refs={
            "dataset_id": "dataset-1",
            "input_keys": ["rows"],
            "previous_event_id": None,
        },
        output_refs={
            "output_keys": ["rows"],
        },
        created_at=datetime(
            2026,
            9,
            14,
            tzinfo=timezone.utc,
        ),
    )


def _audit_event(
    *,
    event_id,
    workspace_id,
    actor_id="owner-1",
    action="CHANGESET_APPLIED",
    resource_id="changeset-1",
    execution_id="execution-1",
    changeset_id="changeset-1",
):
    return SimpleNamespace(
        id=event_id,
        workspace_id=workspace_id,
        actor_id=actor_id,
        action=action,
        resource_type="changeset",
        resource_id=resource_id,
        execution_id=execution_id,
        changeset_id=changeset_id,
        metadata={"status": "APPLIED"},
        created_at=datetime(
            2026,
            9,
            14,
            tzinfo=timezone.utc,
        ),
        previous_hash=None,
        event_hash=f"{event_id}-hash",
    )


class FakeDatasetService:
    def __init__(self, dataset):
        self.dataset = dataset
        self.calls = []

    def get_dataset(self, *, current_user, dataset_id):
        self.calls.append(
            (current_user.user_id, dataset_id)
        )
        return self.dataset


class FakeLineageService:
    def __init__(self, events):
        self.events = events
        self.calls = []

    def list_for_dataset(self, *, dataset_id, owner_id):
        self.calls.append((dataset_id, owner_id))
        return self.events


class FakeAuditService:
    def __init__(self, events):
        self.events = events
        self.calls = []

    def list(self, **kwargs):
        self.calls.append(kwargs)
        return self.events


def test_dataset_lineage_requires_authentication():
    app = create_app(Settings(database_url="sqlite://"))
    client = TestClient(app)

    response = client.get(
        "/datasets/dataset-1/lineage"
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Authentication required"
    }


def test_dataset_lineage_returns_events_for_owned_dataset():
    app, client = _client()

    datasets = FakeDatasetService(_dataset())
    lineage = FakeLineageService([_lineage_event()])

    app.dependency_overrides[get_dataset_service] = (
        lambda: datasets
    )
    app.dependency_overrides[get_lineage_tracking_service] = (
        lambda: lineage
    )

    response = client.get(
        "/datasets/dataset-1/lineage"
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "lineage-1",
            "dataset_id": "dataset-1",
            "execution_id": "execution-1",
            "workflow_id": "workflow-1",
            "workflow_version": "1.0",
            "capability_id": "data.clean",
            "capability_version": "1.0",
            "event_type": "CAPABILITY_EXECUTED",
            "input_refs": {
                "dataset_id": "dataset-1",
                "input_keys": ["rows"],
                "previous_event_id": None,
            },
            "output_refs": {
                "output_keys": ["rows"],
            },
            "created_at": "2026-09-14T00:00:00Z",
        }
    ]

    assert datasets.calls == [
        ("owner-1", "dataset-1"),
    ]
    assert lineage.calls == [
        ("dataset-1", "owner-1"),
    ]


def test_dataset_lineage_returns_empty_list_for_owned_dataset_without_events():
    app, client = _client()

    datasets = FakeDatasetService(_dataset())
    lineage = FakeLineageService([])

    app.dependency_overrides[get_dataset_service] = (
        lambda: datasets
    )
    app.dependency_overrides[get_lineage_tracking_service] = (
        lambda: lineage
    )

    response = client.get(
        "/datasets/dataset-1/lineage"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_dataset_lineage_returns_404_for_dataset_not_owned():
    app, client = _client()

    datasets = FakeDatasetService(None)
    lineage = FakeLineageService([])

    app.dependency_overrides[get_dataset_service] = (
        lambda: datasets
    )
    app.dependency_overrides[get_lineage_tracking_service] = (
        lambda: lineage
    )

    response = client.get(
        "/datasets/other-owner-dataset/lineage"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            "Dataset not found: "
            "other-owner-dataset"
        )
    }
    assert lineage.calls == []


def test_audit_logs_are_owner_scoped_and_filterable():
    app, client = _client()

    audit = FakeAuditService(
        [
            _audit_event(
                event_id="audit-1",
                workspace_id="workspace-1",
            )
        ]
    )

    app.dependency_overrides[get_audit_service] = (
        lambda: audit
    )

    response = client.get(
        "/audit-logs",
        params={
            "workspace_id": "workspace-1",
            "resource_type": "changeset",
            "resource_id": "changeset-1",
            "execution_id": "execution-1",
            "changeset_id": "changeset-1",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["id"] == "audit-1"
    assert body[0]["workspace_id"] == "workspace-1"
    assert body[0]["actor_id"] == "owner-1"
    assert body[0]["event_hash"] == "audit-1-hash"

    assert audit.calls == [
        {
            "owner_id": "owner-1",
            "workspace_id": "workspace-1",
            "resource_type": "changeset",
            "resource_id": "changeset-1",
            "execution_id": "execution-1",
            "changeset_id": "changeset-1",
        }
    ]


def test_audit_logs_require_authentication():
    app = create_app(Settings(database_url="sqlite://"))
    client = TestClient(app)

    response = client.get("/audit-logs")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Authentication required"
    }


def test_audit_logs_can_return_empty_list():
    app, client = _client()

    audit = FakeAuditService([])

    app.dependency_overrides[get_audit_service] = (
        lambda: audit
    )

    response = client.get("/audit-logs")

    assert response.status_code == 200
    assert response.json() == []
