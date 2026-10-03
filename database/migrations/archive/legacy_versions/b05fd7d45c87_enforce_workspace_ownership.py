"""Enforce workspace ownership.

Revision ID: <GIU_NGUYEN_ID_ALEMBIC_TAO>
Revises: 7757af5afe0a
"""

from alembic import op
import sqlalchemy as sa


revision = "b05fd7d45c87"
down_revision = "7757af5afe0a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # Existing ws-demo is legacy/demo data with no real owner.
    # Remove only the known orphaned demo workspace.
    bind.execute(
        sa.text(
            "DELETE FROM workspaces "
            "WHERE id = :workspace_id "
            "AND owner_id IS NULL"
        ),
        {"workspace_id": "ws-demo"},
    )

    with op.batch_alter_table("workspaces") as batch:
        batch.alter_column(
            "owner_id",
            existing_type=sa.String(length=36),
            nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("workspaces") as batch:
        batch.alter_column(
            "owner_id",
            existing_type=sa.String(length=36),
            nullable=True,
        )