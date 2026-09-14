"""link approval requests to immutable changesets

Revision ID: 20260914_02
Revises: 20260914_01
Create Date: 2026-09-14 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260914_02"
down_revision = "20260914_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("approvals") as batch:
        batch.add_column(
            sa.Column(
                "changeset_id",
                sa.String(length=36),
                nullable=False,
            )
        )
        batch.create_index(
            "ix_approvals_changeset_id",
            ["changeset_id"],
        )
        batch.create_foreign_key(
            "fk_approvals_changeset_id_changesets",
            "changesets",
            ["changeset_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("approvals") as batch:
        batch.drop_constraint(
            "fk_approvals_changeset_id_changesets",
            type_="foreignkey",
        )
        batch.drop_index("ix_approvals_changeset_id")
        batch.drop_column("changeset_id")
