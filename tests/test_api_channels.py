from fastapi.testclient import TestClient

from api.dependencies import (
    get_channel_repository,
    get_channel_sync_service,
    get_current_user,
    get_sync_job_repository,
    get_workspace_project_service,
)
from api.main import create_app
from configs.settings import Settings
from domain.channel_sync import (
    Channel,
    ChannelType,
    SyncJob,
    SyncJobStatus,
)
from domain.identity import CurrentUser


USER = CurrentUser(user_id="test-user")
OTHER_USER = CurrentUser(user_id="other-user")


def build_client() -> TestClient:
    app = create_app(
        Settings(
            database_url="sqlite://",
        )
    )
    app.dependency_overrides[get_current_user] = lambda: USER
    return TestClient(app)


class WorkspaceServiceStub:
    def __init__(self, workspaces: dict[str, object]):
        self.workspaces = workspaces

    def get_workspace(self, *, current_user, workspace_id):
        return self.workspaces.get(
            workspace_id
        )


class ChannelRepositoryStub:
    def __init__(self, channels: list[Channel]):
        self.channels = channels

    def list_for_owner(self, *, workspace_id, owner_id):
        return [
            channel
            for channel in self.channels
            if channel.workspace_id == workspace_id
        ]


class ChannelSyncServiceStub:
    def __init__(
        self,
        job: SyncJob | None = None,
        error: ValueError | None = None,
        lookup_job: SyncJob | None = None,
        lookup_owner_id: str = USER.user_id,
    ):
        self.job = job
        self.error = error
        self.lookup_job = lookup_job
        self.lookup_owner_id = lookup_owner_id
        self.calls: list[dict[str, str]] = []
        self.lookup_calls: list[tuple[str, str]] = []

    def sync(self, *, current_user, channel_id, dataset_id, idempotency_key):
        self.calls.append(
            {
                "channel_id": channel_id,
                "dataset_id": dataset_id,
                "idempotency_key": idempotency_key,
            }
        )
        if self.error is not None:
            raise self.error
        assert self.job is not None
        return self.job

    def get_sync_job(self, *, sync_job_id, current_user):
        self.lookup_calls.append(
            (sync_job_id, current_user.user_id)
        )
        if current_user.user_id != self.lookup_owner_id:
            return None
        if self.lookup_job is None or self.lookup_job.id != sync_job_id:
            return None
        return self.lookup_job


def _channel(
    *,
    channel_id: str = "ch-1",
    workspace_id: str = "ws-1",
    enabled: bool = True,
) -> Channel:
    return Channel(
        id=channel_id,
        workspace_id=workspace_id,
        channel=ChannelType.SHOPIFY,
        name="Shopify",
        enabled=enabled,
    )


def _job(
    *,
    job_id: str = "job-1",
    workspace_id: str = "ws-1",
    channel_id: str = "ch-1",
    status: SyncJobStatus = SyncJobStatus.SUCCEEDED,
    error: str | None = None,
) -> SyncJob:
    return SyncJob(
        id=job_id,
        workspace_id=workspace_id,
        dataset_id="ds-1",
        channel_id=channel_id,
        idempotency_key="idem-1",
        status=status,
        error=error,
    )


def test_list_channels_returns_public_channel_fields_without_credentials():
    client = build_client()

    client.app.dependency_overrides[get_workspace_project_service] = lambda: (
        WorkspaceServiceStub({"ws-1": object()})
    )
    client.app.dependency_overrides[get_channel_repository] = lambda: (
        ChannelRepositoryStub([_channel()])
    )

    response = client.get("/channels", params={"workspace_id": "ws-1"})

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "ch-1",
            "workspace_id": "ws-1",
            "channel": "shopify",
            "name": "Shopify",
            "enabled": True,
        }
    ]
    assert "credentials" not in response.text
    assert "credential" not in response.text


def test_list_channels_returns_404_for_workspace_not_owned():
    client = build_client()

    client.app.dependency_overrides[get_workspace_project_service] = lambda: (
        WorkspaceServiceStub({})
    )
    client.app.dependency_overrides[get_channel_repository] = lambda: (
        ChannelRepositoryStub([_channel()])
    )

    response = client.get("/channels", params={"workspace_id": "other-ws"})

    assert response.status_code == 404


def test_sync_channel_returns_sync_job():
    client = build_client()
    stub = ChannelSyncServiceStub(job=_job())

    client.app.dependency_overrides[get_channel_sync_service] = lambda: stub

    response = client.post(
        "/channels/ch-1/sync",
        json={
            "dataset_id": "ds-1",
            "idempotency_key": "idem-1",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": "job-1",
        "workspace_id": "ws-1",
        "dataset_id": "ds-1",
        "channel_id": "ch-1",
        "idempotency_key": "idem-1",
        "status": "succeeded",
        "error": None,
    }
    assert stub.calls == [
        {
            "channel_id": "ch-1",
            "dataset_id": "ds-1",
            "idempotency_key": "idem-1",
        }
    ]


def test_sync_channel_maps_missing_channel_to_404():
    client = build_client()

    client.app.dependency_overrides[get_channel_sync_service] = lambda: (
        ChannelSyncServiceStub(
            error=ValueError("Channel not found: ch-404")
        )
    )

    response = client.post(
        "/channels/ch-404/sync",
        json={
            "dataset_id": "ds-1",
            "idempotency_key": "idem-1",
        },
    )

    assert response.status_code == 404


def test_sync_channel_maps_missing_dataset_to_404():
    client = build_client()

    client.app.dependency_overrides[get_channel_sync_service] = lambda: (
        ChannelSyncServiceStub(
            error=ValueError("Dataset not found: ds-404")
        )
    )

    response = client.post(
        "/channels/ch-1/sync",
        json={
            "dataset_id": "ds-404",
            "idempotency_key": "idem-1",
        },
    )

    assert response.status_code == 404


def test_sync_channel_maps_idempotency_conflict_to_409():
    client = build_client()

    client.app.dependency_overrides[get_channel_sync_service] = lambda: (
        ChannelSyncServiceStub(
            error=ValueError(
                "idempotency_key is already associated with another sync job"
            )
        )
    )

    response = client.post(
        "/channels/ch-1/sync",
        json={
            "dataset_id": "ds-1",
            "idempotency_key": "idem-1",
        },
    )

    assert response.status_code == 409


def test_sync_channel_maps_disabled_channel_to_409():
    client = build_client()

    client.app.dependency_overrides[get_channel_sync_service] = lambda: (
        ChannelSyncServiceStub(
            error=ValueError("Channel is disabled: ch-1")
        )
    )

    response = client.post(
        "/channels/ch-1/sync",
        json={
            "dataset_id": "ds-1",
            "idempotency_key": "idem-1",
        },
    )

    assert response.status_code == 409


def test_sync_channel_rejects_empty_request_fields():
    client = build_client()

    response = client.post(
        "/channels/ch-1/sync",
        json={
            "dataset_id": "",
            "idempotency_key": "",
        },
    )

    assert response.status_code == 422


def test_get_sync_job_returns_owner_scoped_job():
    client = build_client()
    job = _job()
    stub = ChannelSyncServiceStub(
        lookup_job=job,
        lookup_owner_id=USER.user_id,
    )

    client.app.dependency_overrides[get_channel_sync_service] = lambda: stub

    response = client.get("/sync-jobs/job-1")

    assert response.status_code == 200
    assert response.json() == {
        "id": "job-1",
        "workspace_id": "ws-1",
        "dataset_id": "ds-1",
        "channel_id": "ch-1",
        "idempotency_key": "idem-1",
        "status": "succeeded",
        "error": None,
    }
    assert stub.lookup_calls == [("job-1", USER.user_id)]


def test_get_sync_job_returns_404_for_missing_or_other_owner():
    client = build_client()
    stub = ChannelSyncServiceStub()

    client.app.dependency_overrides[get_channel_sync_service] = lambda: stub

    response = client.get("/sync-jobs/job-missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Sync job not found: job-missing"}

    stub.lookup_job = _job()
    stub.lookup_owner_id = OTHER_USER.user_id
    response = client.get("/sync-jobs/job-1")

    assert response.status_code == 404
    assert response.json() == {"detail": "Sync job not found: job-1"}
    assert stub.lookup_calls == [
        ("job-missing", USER.user_id),
        ("job-1", USER.user_id),
    ]


def test_sync_job_response_exposes_error_without_credentials():
    client = build_client()

    job = _job(
        status=SyncJobStatus.FAILED,
        error="remote channel rejected product",
    )

    client.app.dependency_overrides[get_channel_sync_service] = lambda: (
        ChannelSyncServiceStub(
            lookup_job=job,
            lookup_owner_id=USER.user_id,
        )
    )

    response = client.get("/sync-jobs/job-1")

    assert response.status_code == 200
    assert response.json()["error"] == "remote channel rejected product"
    assert "credentials" not in response.text


def test_legacy_sync_job_repository_provider_remains_callable():
    from types import SimpleNamespace

    repository = object()
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                container=SimpleNamespace(sync_jobs=repository),
            ),
        ),
    )

    assert get_sync_job_repository(request) is repository
