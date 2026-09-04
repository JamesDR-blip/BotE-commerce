"""Add transitional workspace ownership.

Revision ID: 7757af5afe0a
Revises: 0001_persistence
"""

from alembic import op
import sqlalchemy as sa


revision = "7757af5afe0a"
down_revision = "0001_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("workspaces") as batch:
        batch.add_column(
            sa.Column(
                "owner_id",
                sa.String(length=36),
                nullable=True,
            )
        )

        batch.create_foreign_key(
            "fk_workspaces_owner_id_users",
            "users",
            ["owner_id"],
            ["id"],
        )

        batch.create_index(
            "ix_workspaces_owner_id",
            ["owner_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("workspaces") as batch:
        batch.drop_index("ix_workspaces_owner_id")
        batch.drop_constraint(
            "fk_workspaces_owner_id_users",
            type_="foreignkey",
        )
        batch.drop_column("owner_id")