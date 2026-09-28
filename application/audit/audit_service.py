"""Application service for tamper-evident audit events."""
from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any, Callable

from sqlalchemy.orm import Session

from domain.audit import (
    AuditEvent,
    compute_audit_event_hash,
    verify_audit_chain,
)
from repositories.audit_events import AuditEventRepository


_SENSITIVE_KEY_FRAGMENTS = frozenset(
    {
        "authorization",
        "access_token",
        "refresh_token",
        "id_token",
        "token",
        "bearer",
        "password",
        "passwd",
        "secret",
        "api_key",
        "apikey",
        "private_key",
        "credential",
        "credentials",
        "cookie",
        "session_token",
        "customer_secret",
    }
)

_SENSITIVE_VALUE_MARKERS = frozenset(
    {
        "bearer ",
        "basic ",
    }
)

_MAX_METADATA_DEPTH = 8
_MAX_STRING_LENGTH = 4096


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")

    return any(
        fragment in normalized
        for fragment in _SENSITIVE_KEY_FRAGMENTS
    )


def _sanitize_value(
    value: Any,
    *,
    depth: int,
) -> Any:
    if depth > _MAX_METADATA_DEPTH:
        return "[REDACTED:MAX_DEPTH]"

    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}

        for key, item in value.items():
            key_string = str(key)

            if _is_sensitive_key(key_string):
                sanitized[key_string] = "[REDACTED]"
                continue

            sanitized[key_string] = _sanitize_value(
                item,
                depth=depth + 1,
            )

        return sanitized

    if isinstance(value, (list, tuple)):
        return [
            _sanitize_value(
                item,
                depth=depth + 1,
            )
            for item in value
        ]

    if isinstance(value, str):
        lowered = value.strip().lower()

        if any(
            lowered.startswith(marker)
            for marker in _SENSITIVE_VALUE_MARKERS
        ):
            return "[REDACTED]"

        if len(value) > _MAX_STRING_LENGTH:
            return value[:_MAX_STRING_LENGTH] + "[TRUNCATED]"

        return value

    if isinstance(value, (int, float, bool)) or value is None:
        return value

    return str(value)


def sanitize_audit_metadata(
    metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return metadata safe for audit persistence."""
    return _sanitize_value(
        dict(metadata or {}),
        depth=0,
    )


class AuditService:
    """Creates immutable workspace-scoped hash-chained audit events."""

    def __init__(
        self,
        sessions: Callable[[], Session],
        repository: AuditEventRepository,
    ) -> None:
        self._sessions = sessions
        self._repository = repository

    def record(
        self,
        *,
        workspace_id: str,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        execution_id: str | None = None,
        changeset_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
    ) -> AuditEvent:
        with self._sessions() as session:
            with session.begin():
                return self.record_in_transaction(
                    session,
                    workspace_id=workspace_id,
                    actor_id=actor_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    execution_id=execution_id,
                    changeset_id=changeset_id,
                    metadata=metadata,
                    created_at=created_at,
                )

    def record_in_transaction(
        self,
        session: Session,
        *,
        workspace_id: str,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        execution_id: str | None = None,
        changeset_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
    ) -> AuditEvent:
        timestamp = created_at or datetime.now(timezone.utc)
        sanitized_metadata = sanitize_audit_metadata(metadata)

        self._repository.lock_workspace(
            session,
            workspace_id,
        )

        previous = self._repository.get_latest_in_transaction(
            session,
            workspace_id,
        )

        previous_hash = (
            previous.event_hash
            if previous is not None
            else None
        )

        event_id = str(uuid.uuid4())

        event_hash = compute_audit_event_hash(
            event_id=event_id,
            workspace_id=workspace_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            execution_id=execution_id,
            changeset_id=changeset_id,
            metadata=sanitized_metadata,
            created_at=timestamp,
            previous_hash=previous_hash,
        )

        event = AuditEvent(
            id=event_id,
            workspace_id=workspace_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            execution_id=execution_id,
            changeset_id=changeset_id,
            metadata=sanitized_metadata,
            created_at=timestamp,
            previous_hash=previous_hash,
            event_hash=event_hash,
        )

        self._repository.add_in_transaction(
            session,
            event,
        )

        return event

    def list(
        self,
        *,
        owner_id: str,
        workspace_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        execution_id: str | None = None,
        changeset_id: str | None = None,
    ) -> list[AuditEvent]:
        events = self._repository.list_for_owner(
            owner_id=owner_id,
            workspace_id=workspace_id,
        )

        events_by_workspace: dict[str, list[AuditEvent]] = {}
        for event in events:
            events_by_workspace.setdefault(
                event.workspace_id,
                [],
            ).append(event)

        for workspace_events in events_by_workspace.values():
            verify_audit_chain(workspace_events)

        if resource_type is not None:
            events = [
                event
                for event in events
                if event.resource_type == resource_type
            ]

        if resource_id is not None:
            events = [
                event
                for event in events
                if event.resource_id == resource_id
            ]

        if execution_id is not None:
            events = [
                event
                for event in events
                if event.execution_id == execution_id
            ]

        if changeset_id is not None:
            events = [
                event
                for event in events
                if event.changeset_id == changeset_id
            ]

        return events
