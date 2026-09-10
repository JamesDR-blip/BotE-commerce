"""Add agent memory persistence.

Revision ID: c13a7e91d204
Revises: b05fd7d45c87
"""

from alembic import op
import sqlalchemy as sa


revision = "c13a7e91d204"
down_revision = "b05fd7d45c87"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("agent_memory"):
        op.create_table(
            "agent_memory",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("workspace_id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("memory_type", sa.String(length=64), nullable=False),
            sa.Column("memory_key", sa.String(length=255), nullable=False),
            sa.Column("value_json", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    existing_indexes = {
        index["name"] for index in sa.inspect(bind).get_indexes("agent_memory")
    }

    indexes = (
        (
            "ix_agent_memory_workspace_id",
            ["workspace_id"],
        ),
        (
            "ix_agent_memory_user_id",
            ["user_id"],
        ),
        (
            "ix_agent_memory_expires_at",
            ["expires_at"],
        ),
        (
            "ix_agent_memory_scope_type_key",
            ["workspace_id", "user_id", "memory_type", "memory_key"],
        ),
    )

    for index_name, columns in indexes:
        if index_name not in existing_indexes:
            op.create_index(
                index_name,
                "agent_memory",
                columns,
                unique=False,
            )


def downgrade() -> None:
    bind = op.get_bind()

    if sa.inspect(bind).has_table("agent_memory"):
        op.drop_table("agent_memory")
