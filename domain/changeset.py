"""Domain model for immutable production ChangeSets."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ChangeSetStatus(str, Enum):
    PREPARED = "PREPARED"
    APPLIED = "APPLIED"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass(frozen=True)
class ChangeSetItem:
    id: str
    changeset_id: str
    entity: str
    record_id: str
    before_snapshot: dict
    after_snapshot: dict


@dataclass(frozen=True)
class ChangeSet:
    id: str
    dataset_id: str
    execution_id: str
    workflow_id: str
    workflow_version: str
    before_storage_key: str
    before_content_hash: str
    after_storage_key: str
    after_content_hash: str
    status: ChangeSetStatus
    created_at: datetime
    applied_at: datetime | None = None
    rolled_back_at: datetime | None = None
    integrity_hash: str | None = None


def canonical_changeset_payload(
    changeset: ChangeSet,
    items: Sequence[ChangeSetItem] = (),
) -> str:
    payload = {
        "id": changeset.id,
        "dataset_id": changeset.dataset_id,
        "execution_id": changeset.execution_id,
        "workflow_id": changeset.workflow_id,
        "workflow_version": changeset.workflow_version,
        "before_storage_key": changeset.before_storage_key,
        "before_content_hash": changeset.before_content_hash,
        "after_storage_key": changeset.after_storage_key,
        "after_content_hash": changeset.after_content_hash,
        "items": [
            {
                "id": item.id,
                "changeset_id": item.changeset_id,
                "entity": item.entity,
                "record_id": item.record_id,
                "before_snapshot": item.before_snapshot,
                "after_snapshot": item.after_snapshot,
            }
            for item in sorted(items, key=lambda value: value.id)
        ],
    }
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def compute_changeset_integrity_hash(
    changeset: ChangeSet,
    items: Sequence[ChangeSetItem] = (),
) -> str:
    return hashlib.sha256(
        canonical_changeset_payload(changeset, items).encode("utf-8")
    ).hexdigest()


def verify_changeset_integrity(
    changeset: ChangeSet,
    items: Sequence[ChangeSetItem] = (),
) -> None:
    if not changeset.integrity_hash:
        raise ValueError(f"ChangeSet {changeset.id} is missing integrity_hash")

    expected_hash = compute_changeset_integrity_hash(changeset, items)
    if changeset.integrity_hash != expected_hash:
        raise ValueError(f"ChangeSet integrity hash mismatch: {changeset.id}")
