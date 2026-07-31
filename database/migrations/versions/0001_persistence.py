"""Add user ownership to the existing execution persistence schema.

Revision ID: 0001_persistence
Revises:
Create Date: 2026-07-31
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0001_persistence"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("email", sa.String(length=255), nullable=False, unique=True),
            sa.Column("display_name", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_users_email", "users", ["email"])
        op.create_index("ix_users_created_at", "users", ["created_at"])
    if "executions" not in tables:
        op.create_table(
            "executions",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("category", sa.String(length=100), nullable=False),
            sa.Column("source_hash", sa.String(length=64), nullable=False),
            sa.Column("rule_version", sa.String(length=64), nullable=False),
            sa.Column("health_score", sa.Float(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="completed"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_executions_user_id", "executions", ["user_id"])
        op.create_index("ix_executions_category", "executions", ["category"])
        op.create_index("ix_executions_source_hash", "executions", ["source_hash"])
        op.create_index("ix_executions_created_at", "executions", ["created_at"])
        op.create_table(
            "validation_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("execution_id", sa.String(length=36), sa.ForeignKey("executions.id"), nullable=False),
            sa.Column("row_number", sa.Integer(), nullable=False),
            sa.Column("field", sa.String(length=100), nullable=False),
            sa.Column("code", sa.String(length=100), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("severity", sa.String(length=20), nullable=False),
        )
        op.create_index("ix_validation_logs_execution_id", "validation_logs", ["execution_id"])
        op.create_table(
            "reports",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("execution_id", sa.String(length=36), sa.ForeignKey("executions.id"), nullable=False),
            sa.Column("format", sa.String(length=12), nullable=False),
            sa.Column("path", sa.Text(), nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
        )
    else:
        columns = {column["name"] for column in inspect(bind).get_columns("executions")}
        if "user_id" not in columns:
            with op.batch_alter_table("executions") as batch:
                batch.add_column(sa.Column("user_id", sa.String(length=36), nullable=True))
                batch.create_foreign_key("fk_executions_user_id_users", "users", ["user_id"], ["id"])
                batch.create_index("ix_executions_user_id", ["user_id"])


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "executions" in tables and "user_id" in {column["name"] for column in inspect(bind).get_columns("executions")}:
        with op.batch_alter_table("executions") as batch:
            batch.drop_index("ix_executions_user_id")
            batch.drop_constraint("fk_executions_user_id_users", type_="foreignkey")
            batch.drop_column("user_id")
    if "users" in tables:
        op.drop_index("ix_users_created_at", table_name="users")
        op.drop_index("ix_users_email", table_name="users")
        op.drop_table("users")
