"""add channel sync jobs and attempts

Revision ID: 20260916_02
Revises: 20260916_01
Create Date: 2026-09-16 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "20260916_02"
down_revision = "20260916_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("channel_id", sa.String(length=36), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
        ),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["channels.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "idempotency_key",
            name="uq_sync_jobs_workspace_idempotency",
        ),
    )

    op.create_index(
        "ix_sync_jobs_workspace_id",
        "sync_jobs",
        ["workspace_id"],
    )
    op.create_index(
        "ix_sync_jobs_dataset_id",
        "sync_jobs",
        ["dataset_id"],
    )
    op.create_index(
        "ix_sync_jobs_channel_id",
        "sync_jobs",
        ["channel_id"],
    )
    op.create_index(
        "ix_sync_jobs_status",
        "sync_jobs",
        ["status"],
    )
    op.create_index(
        "ix_sync_jobs_created_at",
        "sync_jobs",
        ["created_at"],
    )

    op.create_table(
        "sync_attempts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("sync_job_id", sa.String(length=36), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "external_product_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["sync_job_id"],
            ["sync_jobs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "sync_job_id",
            "attempt_number",
            name="uq_sync_attempts_job_attempt",
        ),
    )

    op.create_index(
        "ix_sync_attempts_sync_job_id",
        "sync_attempts",
        ["sync_job_id"],
    )
    op.create_index(
        "ix_sync_attempts_status",
        "sync_attempts",
        ["status"],
    )
    op.create_index(
        "ix_sync_attempts_created_at",
        "sync_attempts",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_sync_attempts_created_at",
        table_name="sync_attempts",
    )
    op.drop_index(
        "ix_sync_attempts_status",
        table_name="sync_attempts",
    )
    op.drop_index(
        "ix_sync_attempts_sync_job_id",
        table_name="sync_attempts",
    )
    op.drop_table("sync_attempts")

    op.drop_index(
        "ix_sync_jobs_created_at",
        table_name="sync_jobs",
    )
    op.drop_index(
        "ix_sync_jobs_status",
        table_name="sync_jobs",
    )
    op.drop_index(
        "ix_sync_jobs_channel_id",
        table_name="sync_jobs",
    )
    op.drop_index(
        "ix_sync_jobs_dataset_id",
        table_name="sync_jobs",
    )
    op.drop_index(
        "ix_sync_jobs_workspace_id",
        table_name="sync_jobs",
    )
    op.drop_table("sync_jobs")
