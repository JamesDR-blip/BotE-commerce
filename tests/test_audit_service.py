from datetime import datetime, timezone

import pytest

from application.audit.audit_service import (
    AuditService,
    sanitize_audit_metadata,
)
from domain.audit import compute_audit_event_hash


class FakeAuditRepository:
    def __init__(self):
        self.events = []
        self.lock_calls = []
        self.latest_calls = []

    def lock_workspace(self, session, workspace_id):
        self.lock_calls.append(workspace_id)
        return object()

    def get_latest_in_transaction(self, session, workspace_id):
        self.latest_calls.append(workspace_id)

        for event in reversed(self.events):
            if event.workspace_id == workspace_id:
                return type(
                    "Record",
                    (),
                    {
                        "event_hash": event.event_hash,
                    },
                )()

        return None

    def add_in_transaction(self, session, event):
        self.events.append(event)
        return event


class FakeSession:
    def begin(self):
        class TransactionContext:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return TransactionContext()


class FakeSessionContext:
    def __init__(self):
        self.session = FakeSession()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeSessions:
    def __call__(self):
        context = FakeSessionContext()

        class TransactionContext:
            def __enter__(self):
                return context.session

            def __exit__(self, exc_type, exc, tb):
                return False

        class SessionContext:
            def __enter__(self):
                return context.session

            def __exit__(self, exc_type, exc, tb):
                return False

            def begin(self):
                return TransactionContext()

        return SessionContext()


def make_service():
    repository = FakeAuditRepository()

    service = AuditService(
        sessions=FakeSessions(),
        repository=repository,
    )

    return service, repository


def test_sanitize_audit_metadata_redacts_sensitive_keys():
    metadata = {
        "authorization": "Bearer abc123",
        "access_token": "secret-token",
        "password": "hunter2",
        "nested": {
            "api_key": "key-value",
            "safe": "visible",
        },
        "normal": "value",
    }

    sanitized = sanitize_audit_metadata(metadata)

    assert sanitized == {
        "authorization": "[REDACTED]",
        "access_token": "[REDACTED]",
        "password": "[REDACTED]",
        "nested": {
            "api_key": "[REDACTED]",
            "safe": "visible",
        },
        "normal": "value",
    }


def test_sanitize_audit_metadata_redacts_bearer_and_basic_values():
    metadata = {
        "header_value": "Bearer abc123",
        "basic_value": "Basic dXNlcjpwYXNz",
        "normal": "Bearerless value",
    }

    sanitized = sanitize_audit_metadata(metadata)

    assert sanitized == {
        "header_value": "[REDACTED]",
        "basic_value": "[REDACTED]",
        "normal": "Bearerless value",
    }


def test_sanitize_audit_metadata_limits_depth():
    value = {
        "level": {
            "level": {
                "level": {
                    "level": {
                        "level": {
                            "level": {
                                "level": {
                                    "level": {
                                        "level": "secret"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    sanitized = sanitize_audit_metadata(value)

    current = sanitized

    for _ in range(8):
        current = current["level"]

    assert current == {"level": "[REDACTED:MAX_DEPTH]"}


def test_sanitize_audit_metadata_truncates_long_strings():
    value = "x" * 5000

    sanitized = sanitize_audit_metadata(
        {"payload": value}
    )

    assert len(sanitized["payload"]) == 4096 + len(
        "[TRUNCATED]"
    )
    assert sanitized["payload"].endswith("[TRUNCATED]")


def test_record_first_event_has_no_previous_hash():
    service, repository = make_service()

    created_at = datetime(
        2026,
        9,
        14,
        10,
        0,
        tzinfo=timezone.utc,
    )

    event = service.record(
        workspace_id="workspace-1",
        actor_id="user-1",
        action="CHANGESET_APPLIED",
        resource_type="changeset",
        resource_id="changeset-1",
        execution_id="execution-1",
        changeset_id="changeset-1",
        metadata={"status": "APPLIED"},
        created_at=created_at,
    )

    assert event.previous_hash is None
    assert event.event_hash is not None
    assert len(event.event_hash) == 64

    expected_hash = compute_audit_event_hash(
        event_id=event.id,
        workspace_id=event.workspace_id,
        actor_id=event.actor_id,
        action=event.action,
        resource_type=event.resource_type,
        resource_id=event.resource_id,
        execution_id=event.execution_id,
        changeset_id=event.changeset_id,
        metadata=event.metadata,
        created_at=created_at,
        previous_hash=None,
    )

    assert event.event_hash == expected_hash
    assert repository.events == [event]


def test_record_second_event_chains_to_previous_event():
    service, repository = make_service()

    created_at = datetime(
        2026,
        9,
        14,
        10,
        0,
        tzinfo=timezone.utc,
    )

    first = service.record(
        workspace_id="workspace-1",
        actor_id="user-1",
        action="CHANGESET_APPLIED",
        resource_type="changeset",
        resource_id="changeset-1",
        metadata={"status": "APPLIED"},
        created_at=created_at,
    )

    second = service.record(
        workspace_id="workspace-1",
        actor_id="user-1",
        action="EXECUTION_COMPLETED",
        resource_type="execution",
        resource_id="execution-1",
        metadata={"status": "COMPLETED"},
        created_at=created_at,
    )

    assert second.previous_hash == first.event_hash
    assert second.event_hash != first.event_hash

    expected_hash = compute_audit_event_hash(
        event_id=second.id,
        workspace_id=second.workspace_id,
        actor_id=second.actor_id,
        action=second.action,
        resource_type=second.resource_type,
        resource_id=second.resource_id,
        execution_id=second.execution_id,
        changeset_id=second.changeset_id,
        metadata=second.metadata,
        created_at=created_at,
        previous_hash=first.event_hash,
    )

    assert second.event_hash == expected_hash

    assert repository.lock_calls == [
        "workspace-1",
        "workspace-1",
    ]
    assert repository.latest_calls == [
        "workspace-1",
        "workspace-1",
    ]


def test_record_sanitizes_metadata_before_hashing_and_persistence():
    service, repository = make_service()

    event = service.record(
        workspace_id="workspace-1",
        actor_id="user-1",
        action="DATA_ACCESS",
        resource_type="dataset",
        resource_id="dataset-1",
        metadata={
            "authorization": "Bearer should-not-persist",
            "password": "should-not-persist",
            "safe": "visible",
        },
    )

    assert event.metadata == {
        "authorization": "[REDACTED]",
        "password": "[REDACTED]",
        "safe": "visible",
    }

    persisted = repository.events[0]

    assert persisted.metadata == event.metadata
    assert "should-not-persist" not in str(
        persisted.metadata
    )


def test_record_in_transaction_uses_same_session_and_creates_event():
    service, repository = make_service()

    session = FakeSession()

    event = service.record_in_transaction(
        session,
        workspace_id="workspace-1",
        actor_id="user-1",
        action="ROLLBACK_COMPLETED",
        resource_type="changeset",
        resource_id="changeset-1",
        changeset_id="changeset-1",
    )

    assert event.id
    assert event.event_hash
    assert repository.events == [event]
    assert repository.lock_calls == ["workspace-1"]
    assert repository.latest_calls == ["workspace-1"]


def test_record_in_transaction_rejects_missing_workspace():
    class MissingWorkspaceRepository(FakeAuditRepository):
        def lock_workspace(self, session, workspace_id):
            raise ValueError(
                f"Workspace not found: {workspace_id}"
            )

    repository = MissingWorkspaceRepository()

    service = AuditService(
        sessions=FakeSessions(),
        repository=repository,
    )

    with pytest.raises(
        ValueError,
        match="Workspace not found: workspace-missing",
    ):
        service.record(
            workspace_id="workspace-missing",
            actor_id="user-1",
            action="TEST",
            resource_type="test",
            resource_id="test-1",
        )

    assert repository.events == []

