"""Add persistent storage reference to datasets.

Revision ID: d14c1f2a9b31
Revises: c13a7e91d204
"""

from alembic import op
import sqlalchemy as sa


revision = "d14c1f2a9b31"
down_revision = "c13a7e91d204"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {
        column["name"]
        for column in inspector.get_columns("datasets")
    }

    if "storage_key" not in columns:
        op.add_column(
            "datasets",
            sa.Column("storage_key", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {
        column["name"]
        for column in inspector.get_columns("datasets")
    }

    if "storage_key" in columns:
        op.drop_column("datasets", "storage_key")
