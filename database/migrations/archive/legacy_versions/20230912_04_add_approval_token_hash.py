"""add hashed approval token

Revision ID: 20230912_04
Revises: 20230912_03
Create Date: 2026-09-12 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20230912_04"
down_revision = "20230912_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("approvals") as batch:
        batch.add_column(
            sa.Column(
                "token_hash",
                sa.String(length=64),
                nullable=False,
                server_default="",
            )
        )

    with op.batch_alter_table("approvals") as batch:
        batch.alter_column(
            "token_hash",
            existing_type=sa.String(length=64),
            server_default=None,
        )


def downgrade() -> None:
    with op.batch_alter_table("approvals") as batch:
        batch.drop_column("token_hash")
