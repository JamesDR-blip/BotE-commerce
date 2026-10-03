"""add immutable changesets and changeset items

Revision ID: 20260914_01
Revises: 20230912_04
Create Date: 2026-09-14 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260914_01"
down_revision = "20230912_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "changesets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "dataset_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "execution_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "workflow_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "workflow_version",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "before_storage_key",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "before_content_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "after_storage_key",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "after_content_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "applied_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "rolled_back_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
        ),
        sa.ForeignKeyConstraint(
            ["execution_id"],
            ["workflow_executions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workflow_id"],
            ["workflows.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_changesets_dataset_id",
        "changesets",
        ["dataset_id"],
    )
    op.create_index(
        "ix_changesets_execution_id",
        "changesets",
        ["execution_id"],
    )
    op.create_index(
        "ix_changesets_workflow_id",
        "changesets",
        ["workflow_id"],
    )
    op.create_index(
        "ix_changesets_status",
        "changesets",
        ["status"],
    )
    op.create_index(
        "ix_changesets_created_at",
        "changesets",
        ["created_at"],
    )

    op.create_table(
        "changeset_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "changeset_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "entity",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "record_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "before_snapshot",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "after_snapshot",
            sa.JSON(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["changeset_id"],
            ["changesets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_changeset_items_changeset_id",
        "changeset_items",
        ["changeset_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_changeset_items_changeset_id",
        table_name="changeset_items",
    )
    op.drop_table("changeset_items")

    op.drop_index(
        "ix_changesets_created_at",
        table_name="changesets",
    )
    op.drop_index(
        "ix_changesets_status",
        table_name="changesets",
    )
    op.drop_index(
        "ix_changesets_workflow_id",
        table_name="changesets",
    )
    op.drop_index(
        "ix_changesets_execution_id",
        table_name="changesets",
    )
    op.drop_index(
        "ix_changesets_dataset_id",
        table_name="changesets",
    )
    op.drop_table("changesets")
