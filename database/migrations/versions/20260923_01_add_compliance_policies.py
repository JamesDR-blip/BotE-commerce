"""add organization compliance policies

Revision ID: 20260923_01
Revises: 20260922_01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260923_01"
down_revision = "20260922_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "compliance_policies",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "organization_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("resource", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column(
            "condition",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "name",
            name="uq_compliance_policy_organization_name",
        ),
    )

    op.create_index(
        "ix_compliance_policies_organization_id",
        "compliance_policies",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_compliance_policies_organization_id",
        table_name="compliance_policies",
    )
    op.drop_table("compliance_policies")
