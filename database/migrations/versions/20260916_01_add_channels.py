"""add workspace-owned channel connections

Revision ID: 20260916_01
Revises: 20260914_03
Create Date: 2026-09-16 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260916_01"
down_revision = "20260914_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "channels",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "workspace_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "channel_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "credentials_encrypted",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "channel_type",
            "name",
            name="uq_channels_workspace_channel_name",
        ),
    )

    op.create_index(
        "ix_channels_workspace_id",
        "channels",
        ["workspace_id"],
    )
    op.create_index(
        "ix_channels_created_at",
        "channels",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_channels_created_at",
        table_name="channels",
    )
    op.drop_index(
        "ix_channels_workspace_id",
        table_name="channels",
    )
    op.drop_table("channels")
