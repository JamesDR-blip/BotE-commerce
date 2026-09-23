"""Add organization quota persistence."""

from alembic import op
import sqlalchemy as sa


revision = "20260922_01"
down_revision = "20260916_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization_quotas",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "organization_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "dimension",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "limit",
            sa.Integer(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "dimension",
            name="uq_organization_quota_dimension",
        ),
    )
    op.create_index(
        "ix_organization_quotas_organization_id",
        "organization_quotas",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_organization_quotas_organization_id",
        table_name="organization_quotas",
    )
    op.drop_table("organization_quotas")
