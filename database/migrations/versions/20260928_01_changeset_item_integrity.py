"""include immutable ChangeSet items in the integrity commitment

Revision ID: 20260928_01
Revises: 20260926_01
Create Date: 2026-09-28
"""

from __future__ import annotations

import hashlib
import json

import sqlalchemy as sa
from alembic import op

revision = "20260928_01"
down_revision = "20260926_01"
branch_labels = None
depends_on = None


def _integrity_hash(
    changeset_row: tuple[object, ...],
    item_rows: list[tuple[object, ...]],
) -> str:
    keys = (
        "id",
        "dataset_id",
        "execution_id",
        "workflow_id",
        "workflow_version",
        "before_storage_key",
        "before_content_hash",
        "after_storage_key",
        "after_content_hash",
    )
    payload = dict(zip(keys, changeset_row, strict=True))
    payload["items"] = []
    for row in item_rows:
        item_payload = dict(
            zip(
                (
                    "id",
                    "changeset_id",
                    "entity",
                    "record_id",
                    "before_snapshot",
                    "after_snapshot",
                ),
                row,
                strict=True,
            )
        )
        for snapshot_key in ("before_snapshot", "after_snapshot"):
            snapshot = item_payload[snapshot_key]
            if isinstance(snapshot, str):
                item_payload[snapshot_key] = json.loads(snapshot)
        payload["items"].append(item_payload)
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text("""
            SELECT id,
                   dataset_id,
                   execution_id,
                   workflow_id,
                   workflow_version,
                   before_storage_key,
                   before_content_hash,
                   after_storage_key,
                   after_content_hash
            FROM changesets
            ORDER BY id
            """)).fetchall()

    for row in rows:
        items = bind.execute(
            sa.text("""
                SELECT id,
                       changeset_id,
                       entity,
                       record_id,
                       before_snapshot,
                       after_snapshot
                FROM changeset_items
                WHERE changeset_id = :changeset_id
                ORDER BY id
                """),
            {"changeset_id": row[0]},
        ).fetchall()
        bind.execute(
            sa.text("""
                UPDATE changesets
                SET integrity_hash = :integrity_hash
                WHERE id = :id
                """),
            {
                "id": row[0],
                "integrity_hash": _integrity_hash(row, items),
            },
        )


def downgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text("""
            SELECT id,
                   dataset_id,
                   execution_id,
                   workflow_id,
                   workflow_version,
                   before_storage_key,
                   before_content_hash,
                   after_storage_key,
                   after_content_hash
            FROM changesets
            ORDER BY id
            """)).fetchall()
    keys = (
        "id",
        "dataset_id",
        "execution_id",
        "workflow_id",
        "workflow_version",
        "before_storage_key",
        "before_content_hash",
        "after_storage_key",
        "after_content_hash",
    )
    for row in rows:
        canonical = json.dumps(
            dict(zip(keys, row, strict=True)),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        bind.execute(
            sa.text("UPDATE changesets SET integrity_hash = :hash WHERE id = :id"),
            {
                "id": row[0],
                "hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            },
        )
