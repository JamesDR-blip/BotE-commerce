"""add foreign key to approvals table linking to workflow_executions

Revision ID: 20230912_02
Revises: 20230912_01
Create Date: 2026-09-12 16:05:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20230912_02"
down_revision = "20230912_01"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add foreign key constraint from approvals.execution_id to workflow_executions.id
    with op.batch_alter_table("approvals") as batch:
        batch.create_foreign_key(
            "fk_approvals_execution_id_workflow_executions",
            "workflow_executions",
            ["execution_id"],
            ["id"],
        )

def downgrade() -> None:
    with op.batch_alter_table("approvals") as batch:
        batch.drop_index("ix_approvals_execution_id")
        batch.drop_constraint("fk_approvals_execution_id_workflow_executions", type_="foreignkey")
