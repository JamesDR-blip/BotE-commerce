"""create workspaces

Revision ID: fcbc1a52044c
Revises: 20230912_02
Create Date: 2026-09-12 16:03:43.995688

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fcbc1a52044c'
down_revision: Union[str, Sequence[str], None] = '20230912_02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create workspaces table
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
