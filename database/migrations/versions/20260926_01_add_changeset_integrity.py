"""add cryptographic integrity commitment to ChangeSets

Revision ID: 20260926_01
Revises: 20260923_01
Create Date: 2026-09-26
"""

from __future__ import annotations

import hashlib
import json

from alembic import op
import sqlalchemy as sa


revision = "20260926_01"
down_revision = "20260923_01"
branch_labels = None
depends_on = None


def _integrity_hash(row: tuple[object, ...]) -> str:
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
    payload = dict(zip(keys, row, strict=True))
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def upgrade() -> None:
    op.add_column(
        "changesets",
        sa.Column(
            "integrity_hash",
            sa.String(length=64),
            nullable=True,
        ),
    )

    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
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
            """
        )
    ).fetchall()

    for row in rows:
        bind.execute(
            sa.text(
                """
                UPDATE changesets
                SET integrity_hash = :integrity_hash
                WHERE id = :id
                """
            ),
            {
                "id": row[0],
                "integrity_hash": _integrity_hash(row),
            },
        )

    with op.batch_alter_table("changesets") as batch_op:
        batch_op.alter_column(
            "integrity_hash",
            existing_type=sa.String(length=64),
            nullable=False,
        )


def downgrade() -> None:
    op.drop_column("changesets", "integrity_hash")
