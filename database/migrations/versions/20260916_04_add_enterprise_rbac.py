"""Add enterprise RBAC persistence foundation."""

from alembic import op
import sqlalchemy as sa


revision = "20260916_04"
down_revision = "20260916_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_organizations_created_at",
        "organizations",
        ["created_at"],
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("resource", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "resource",
            "action",
            name="uq_permissions_resource_action",
        ),
    )

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.String(length=36), nullable=False),
        sa.Column("permission_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"]),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
        sa.UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permissions_role_permission",
        ),
    )

    op.create_table(
        "memberships",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("role_id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "organization_id",
            "role_id",
            name="uq_memberships_user_org_role",
        ),
    )
    op.create_index(
        "ix_memberships_user_id",
        "memberships",
        ["user_id"],
    )
    op.create_index(
        "ix_memberships_organization_id",
        "memberships",
        ["organization_id"],
    )
    op.create_index(
        "ix_memberships_role_id",
        "memberships",
        ["role_id"],
    )
    op.create_index(
        "ix_memberships_created_at",
        "memberships",
        ["created_at"],
    )

    with op.batch_alter_table("workspaces") as batch:
        batch.add_column(
            sa.Column(
                "organization_id",
                sa.String(length=36),
                nullable=True,
            )
        )
        batch.create_foreign_key(
            "fk_workspaces_organization_id",
            "organizations",
            ["organization_id"],
            ["id"],
        )
        batch.create_index(
            "ix_workspaces_organization_id",
            ["organization_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("workspaces") as batch:
        batch.drop_index("ix_workspaces_organization_id")
        batch.drop_constraint(
            "fk_workspaces_organization_id",
            type_="foreignkey",
        )
        batch.drop_column("organization_id")

    op.drop_index(
        "ix_memberships_created_at",
        table_name="memberships",
    )
    op.drop_index(
        "ix_memberships_role_id",
        table_name="memberships",
    )
    op.drop_index(
        "ix_memberships_organization_id",
        table_name="memberships",
    )
    op.drop_index(
        "ix_memberships_user_id",
        table_name="memberships",
    )
    op.drop_table("memberships")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")

    op.drop_index(
        "ix_organizations_created_at",
        table_name="organizations",
    )
    op.drop_table("organizations")
