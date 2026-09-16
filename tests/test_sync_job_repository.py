from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database.models import Base, SyncAttemptRecord, SyncJobRecord
from domain.channel_sync import (
    SyncAttempt,
    SyncAttemptStatus,
    SyncJob,
    SyncJobStatus,
)
from repositories.sync_jobs import (
    SyncAttemptRepository,
    SyncJobRepository,
)
from repositories.workspaces import WorkspaceRepository


def create_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


def create_workspace(
    sessions,
    *,
    workspace_id="ws-1",
    owner_id="user-1",
):
    WorkspaceRepository(sessions).create(
        workspace_id=workspace_id,
        owner_id=owner_id,
        name=f"Workspace {workspace_id}",
    )


def make_job(
    *,
    job_id="job-1",
    workspace_id="ws-1",
    dataset_id="dataset-1",
    channel_id="ch-1",
    key="sync-key-1",
    status=SyncJobStatus.QUEUED,
    error=None,
):
    return SyncJob(
        id=job_id,
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        channel_id=channel_id,
        idempotency_key=key,
        status=status,
        error=error,
    )


def test_sync_job_repository_round_trip_and_owner_scope():
    sessions = create_session()
    create_workspace(sessions)

    repository = SyncJobRepository(sessions)
    created = repository.create(job=make_job())

    assert created == make_job()
    assert repository.get("job-1") == make_job()
    assert repository.get_for_owner(
        job_id="job-1",
        owner_id="user-1",
    ) == make_job()
    assert repository.get_for_owner(
        job_id="job-1",
        owner_id="user-2",
    ) is None


def test_sync_job_repository_idempotency_lookup_is_owner_scoped():
    sessions = create_session()
    create_workspace(sessions)

    repository = SyncJobRepository(sessions)
    repository.create(job=make_job())

    assert repository.get_by_idempotency_key_for_owner(
        workspace_id="ws-1",
        owner_id="user-1",
        idempotency_key="sync-key-1",
    ) == make_job()

    assert repository.get_by_idempotency_key_for_owner(
        workspace_id="ws-1",
        owner_id="user-2",
        idempotency_key="sync-key-1",
    ) is None


def test_sync_job_repository_enforces_workspace_idempotency():
    sessions = create_session()
    create_workspace(sessions)

    repository = SyncJobRepository(sessions)
    repository.create(job=make_job())

    duplicate = make_job(job_id="job-2")

    try:
        repository.create(job=duplicate)
    except IntegrityError:
        pass
    else:
        raise AssertionError("expected IntegrityError")


def test_sync_job_repository_update_persists_state():
    sessions = create_session()
    create_workspace(sessions)

    repository = SyncJobRepository(sessions)
    repository.create(job=make_job())

    running = make_job(
        status=SyncJobStatus.RUNNING,
    )

    updated = repository.update(job=running)

    assert updated.status is SyncJobStatus.RUNNING
    assert repository.get("job-1").status is SyncJobStatus.RUNNING


def test_sync_attempt_repository_round_trip_and_ordering():
    sessions = create_session()
    create_workspace(sessions)

    jobs = SyncJobRepository(sessions)
    attempts = SyncAttemptRepository(sessions)

    jobs.create(job=make_job())

    attempts.create(
        attempt=SyncAttempt(
            id="attempt-2",
            sync_job_id="job-1",
            attempt_number=2,
            status=SyncAttemptStatus.FAILED,
            request_hash="b" * 64,
            error="temporary failure",
        )
    )
    attempts.create(
        attempt=SyncAttempt(
            id="attempt-1",
            sync_job_id="job-1",
            attempt_number=1,
            status=SyncAttemptStatus.SUCCEEDED,
            request_hash="a" * 64,
            external_product_id="external-1",
        )
    )

    loaded = attempts.list_for_job(sync_job_id="job-1")

    assert [item.attempt_number for item in loaded] == [1, 2]
    assert loaded[0].external_product_id == "external-1"
    assert loaded[1].error == "temporary failure"


def test_sync_attempt_repository_enforces_attempt_number_uniqueness():
    sessions = create_session()
    create_workspace(sessions)

    jobs = SyncJobRepository(sessions)
    attempts = SyncAttemptRepository(sessions)

    jobs.create(job=make_job())

    first = SyncAttempt(
        id="attempt-1",
        sync_job_id="job-1",
        attempt_number=1,
        status=SyncAttemptStatus.SUCCEEDED,
        request_hash="a" * 64,
        external_product_id="external-1",
    )

    attempts.create(attempt=first)

    duplicate = SyncAttempt(
        id="attempt-2",
        sync_job_id="job-1",
        attempt_number=1,
        status=SyncAttemptStatus.SUCCEEDED,
        request_hash="b" * 64,
        external_product_id="external-2",
    )

    try:
        attempts.create(attempt=duplicate)
    except IntegrityError:
        pass
    else:
        raise AssertionError("expected IntegrityError")
