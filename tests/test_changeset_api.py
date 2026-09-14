from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from api.dependencies import (
    get_changeset_query_service,
    get_changeset_rollback_service,
    get_current_user,
)
from api.main import create_app
from configs.settings import Settings
from domain.changeset import ChangeSetStatus
from domain.identity import CurrentUser


def _changeset(
    *,
    changeset_id: str = "cs-1",
    status: ChangeSetStatus = ChangeSetStatus.PREPARED,
):
    return SimpleNamespace(
        id=changeset_id,
        dataset_id="dataset-1",
        execution_id="execution-1",
        workflow_id="workflow-1",
        workflow_version="1.0",
        before_content_hash="a" * 64,
        after_content_hash="b" * 64,
        status=status,
        created_at=datetime(2026, 9, 14, tzinfo=timezone.utc),
        applied_at=None,
        rolled_back_at=None,
    )


def _item():
    return SimpleNamespace(
        id="item-1",
        changeset_id="cs-1",
        entity="dataset_row",
        record_id="0",
        before_snapshot={"name": "old", "price": 10},
        after_snapshot={"name": "new", "price": 20},
    )


class FakeQueryService:
    def __init__(self, changeset=None, items=None):
        self.changeset = changeset
        self.items = items if items is not None else [_item()]
        self.calls = []

    def list_changesets(self, *, current_user):
        self.calls.append(("list", current_user.user_id))
        return [self.changeset] if self.changeset is not None else []

    def get_changeset(self, *, current_user, changeset_id):
        self.calls.append(
            ("get", current_user.user_id, changeset_id)
        )
        if self.changeset is None:
            return None
        if self.changeset.id != changeset_id:
            return None
        return self.changeset

    def get_items(self, *, current_user, changeset_id):
        self.calls.append(
            ("items", current_user.user_id, changeset_id)
        )
        if self.changeset is None:
            return None
        if self.changeset.id != changeset_id:
            return None
        return self.items


class FakeRollbackService:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def rollback(self, *, changeset_id):
        self.calls.append(changeset_id)
        if self.error is not None:
            raise self.error
        return self.result


def _client(query_service, rollback_service):
    app = create_app(Settings(database_url="sqlite://"))

    current_user = CurrentUser(user_id="test-user")

    app.dependency_overrides[get_current_user] = (
        lambda: current_user
    )
    app.dependency_overrides[get_changeset_query_service] = (
        lambda: query_service
    )
    app.dependency_overrides[get_changeset_rollback_service] = (
        lambda: rollback_service
    )

    return TestClient(app)


def test_list_changesets_endpoint():
    query = FakeQueryService(_changeset())
    client = _client(query, FakeRollbackService())

    response = client.get("/changesets")

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["id"] == "cs-1"
    assert body[0]["dataset_id"] == "dataset-1"
    assert body[0]["status"] == "PREPARED"

    assert query.calls == [
        ("list", "test-user"),
    ]


def test_get_changeset_endpoint_returns_detail_and_items():
    query = FakeQueryService(_changeset())
    client = _client(query, FakeRollbackService())

    response = client.get("/changesets/cs-1")

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == "cs-1"
    assert body["status"] == "PREPARED"
    assert len(body["items"]) == 1
    assert body["items"][0] == {
        "id": "item-1",
        "changeset_id": "cs-1",
        "entity": "dataset_row",
        "record_id": "0",
        "before_snapshot": {
            "name": "old",
            "price": 10,
        },
        "after_snapshot": {
            "name": "new",
            "price": 20,
        },
    }


def test_get_changeset_endpoint_returns_404_for_missing_changeset():
    query = FakeQueryService(None)
    client = _client(query, FakeRollbackService())

    response = client.get("/changesets/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "ChangeSet not found: missing"
    )


def test_rollback_changeset_endpoint():
    original = _changeset()
    rolled_back = _changeset(
        status=ChangeSetStatus.ROLLED_BACK,
    )
    rolled_back.rolled_back_at = datetime(
        2026, 9, 14, 1, tzinfo=timezone.utc
    )

    query = FakeQueryService(original)
    rollback = FakeRollbackService(result=rolled_back)

    client = _client(query, rollback)

    response = client.post("/changesets/cs-1/rollback")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "rollback_completed"
    assert body["changeset"]["id"] == "cs-1"
    assert body["changeset"]["status"] == "ROLLED_BACK"

    assert rollback.calls == ["cs-1"]


def test_rollback_changeset_endpoint_returns_404_for_missing_changeset():
    query = FakeQueryService(None)
    rollback = FakeRollbackService()

    client = _client(query, rollback)

    response = client.post("/changesets/missing/rollback")

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "ChangeSet not found: missing"
    )
    assert rollback.calls == []


def test_rollback_changeset_endpoint_maps_value_error_to_409():
    query = FakeQueryService(_changeset())
    rollback = FakeRollbackService(
        error=ValueError(
            "ChangeSet cs-1 is not currently APPLIED"
        )
    )

    client = _client(query, rollback)

    response = client.post("/changesets/cs-1/rollback")

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "ChangeSet cs-1 is not currently APPLIED"
    )
