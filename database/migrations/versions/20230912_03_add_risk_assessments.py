"""add risk assessment persistence

Revision ID: 20230912_03
Revises: fcbc1a52044c
Create Date: 2026-09-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20230912_03"
down_revision = "fcbc1a52044c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "risk_assessments",
        sa.Column(
            "id",
            sa.String(length=36),
            primary_key=True,
        ),
        sa.Column(
            "execution_id",
            sa.String(length=36),
            sa.ForeignKey("workflow_executions.id"),
            nullable=False,
        ),
        sa.Column(
            "risk_score",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "confidence_score",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "approval_required",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_risk_assessments_execution_id",
        "risk_assessments",
        ["execution_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_risk_assessments_execution_id",
        table_name="risk_assessments",
    )
    op.drop_table("risk_assessments")
