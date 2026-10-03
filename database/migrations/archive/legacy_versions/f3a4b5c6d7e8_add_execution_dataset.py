"""Add dataset reference to validation executions.

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
"""

from alembic import op
import sqlalchemy as sa


revision = "f3a4b5c6d7e8"
down_revision = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = {
        column["name"]
        for column in inspector.get_columns("executions")
    }

    if "dataset_id" not in columns:
        with op.batch_alter_table("executions") as batch:
            batch.add_column(
                sa.Column(
                    "dataset_id",
                    sa.String(length=36),
                    nullable=True,
                )
            )
            batch.create_foreign_key(
                "fk_executions_dataset_id_datasets",
                "datasets",
                ["dataset_id"],
                ["id"],
            )
            batch.create_index(
                "ix_executions_dataset_id",
                ["dataset_id"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = {
        column["name"]
        for column in inspector.get_columns("executions")
    }

    if "dataset_id" in columns:
        with op.batch_alter_table("executions") as batch:
            batch.drop_index("ix_executions_dataset_id")
            batch.drop_constraint(
                "fk_executions_dataset_id_datasets",
                type_="foreignkey",
            )
            batch.drop_column("dataset_id")
