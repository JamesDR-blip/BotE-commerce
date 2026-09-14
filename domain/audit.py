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
