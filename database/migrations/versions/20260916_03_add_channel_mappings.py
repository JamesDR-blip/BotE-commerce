"""Add persisted channel mappings."""

from alembic import op
import sqlalchemy as sa


revision = "20260916_03"
down_revision = "20260916_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "channel_mappings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("channel_id", sa.String(length=36), nullable=False),
        sa.Column(
            "canonical_product_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("channel_type", sa.String(length=50), nullable=False),
        sa.Column(
            "external_product_id",
            sa.String(length=255),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "last_synced_hash",
            sa.String(length=64),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["channels.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "channel_id",
            "canonical_product_id",
            name="uq_channel_mappings_channel_product",
        ),
    )
    op.create_index(
        "ix_channel_mappings_channel_id",
        "channel_mappings",
        ["channel_id"],
    )
    op.create_index(
        "ix_channel_mappings_canonical_product_id",
        "channel_mappings",
        ["canonical_product_id"],
    )
    op.create_index(
        "ix_channel_mappings_created_at",
        "channel_mappings",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_channel_mappings_created_at",
        table_name="channel_mappings",
    )
    op.drop_index(
        "ix_channel_mappings_canonical_product_id",
        table_name="channel_mappings",
    )
    op.drop_index(
        "ix_channel_mappings_channel_id",
        table_name="channel_mappings",
    )
    op.drop_table("channel_mappings")
