"""Domain model for immutable production ChangeSets."""

from __future__ import annotations

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
