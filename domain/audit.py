"""Domain contracts and deterministic hashing for audit events."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    id: str
    workspace_id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    execution_id: str | None = None
    changeset_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    previous_hash: str | None = None
    event_hash: str | None = None


def canonical_audit_payload(
    *,
    event_id: str,
    workspace_id: str,
    actor_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    execution_id: str | None,
    changeset_id: str | None,
    metadata: dict[str, Any],
    created_at: datetime,
    previous_hash: str | None,
) -> str:
    """Return the canonical representation used for audit hashing."""
    payload = {
        "id": event_id,
        "workspace_id": workspace_id,
        "actor_id": actor_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "execution_id": execution_id,
        "changeset_id": changeset_id,
        "metadata": metadata,
        "created_at": created_at.isoformat(),
        "previous_hash": previous_hash,
    }

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def compute_audit_event_hash(
    *,
    event_id: str,
    workspace_id: str,
    actor_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    execution_id: str | None,
    changeset_id: str | None,
    metadata: dict[str, Any],
    created_at: datetime,
    previous_hash: str | None,
) -> str:
    canonical = canonical_audit_payload(
        event_id=event_id,
        workspace_id=workspace_id,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        execution_id=execution_id,
        changeset_id=changeset_id,
        metadata=metadata,
        created_at=created_at,
        previous_hash=previous_hash,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()
from collections.abc import Sequence


def verify_audit_event_hash(event: AuditEvent) -> None:
    """Raise ValueError when an audit event hash does not match its payload."""
    if not event.event_hash:
        raise ValueError(
            f"Audit event {event.id} is missing event_hash"
        )

    if event.created_at is None:
        raise ValueError(
            f"Audit event {event.id} is missing created_at"
        )

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
        created_at=event.created_at,
        previous_hash=event.previous_hash,
    )

    if event.event_hash != expected_hash:
        raise ValueError(
            f"Audit event hash mismatch: {event.id}"
        )


def verify_audit_chain(events: Sequence[AuditEvent]) -> None:
    """Raise ValueError when an audit event chain is invalid."""
    previous: AuditEvent | None = None

    for event in events:
        if previous is not None and event.workspace_id != previous.workspace_id:
            raise ValueError(
                "Audit chain contains events from different workspaces"
            )

        expected_previous_hash = (
            previous.event_hash
            if previous is not None
            else None
        )

        if event.previous_hash != expected_previous_hash:
            raise ValueError(
                f"Audit chain previous_hash mismatch: {event.id}"
            )

        verify_audit_event_hash(event)
        previous = event
