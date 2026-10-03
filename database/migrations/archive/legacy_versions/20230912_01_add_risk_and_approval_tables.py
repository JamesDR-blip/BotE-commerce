"""add risk and approval tables

Revision ID: 20230912_01
Revises: f3a4b5c6d7e8
Create Date: 2026-09-12 15:57:30.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20230912_01"
down_revision = "f3a4b5c6d7e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "risk_policies",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "high_risk_threshold",
            sa.Float,
            nullable=False,
            server_default=sa.text("0.7"),
        ),
        sa.Column(
            "critical_risk_threshold",
            sa.Float,
            nullable=False,
            server_default=sa.text("0.9"),
        ),
    )

    op.create_table(
        "approvals",
        sa.Column("approval_id", sa.String(length=36), primary_key=True),
        sa.Column(
            "execution_id",
            sa.String(length=36),
            nullable=False,
            index=True,
        ),
        sa.Column("risk_score", sa.String(length=20), nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=False),
        sa.Column("requested_by", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "decision",
            sa.String(length=20),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("approvals")
    op.drop_table("risk_policies")
