from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from repositories.rbac import RBACRepository


def make_repository() -> RBACRepository:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    return RBACRepository(sessions)


def test_rbac_repository_resolves_permissions_through_membership() -> None:
    repository = make_repository()

    repository.create_role(
        role_id="role-admin",
        name="admin",
    )
    repository.create_permission(
        permission_id="permission-workflow-execute",
        resource="workflow",
        action="execute",
    )
    repository.assign_permission_to_role(
        role_id="role-admin",
        permission_id="permission-workflow-execute",
    )
    repository.create_membership(
        membership_id="membership-1",
        user_id="user-1",
        organization_id="org-1",
        role_id="role-admin",
    )

    assert repository.has_permission(
        user_id="user-1",
        permission_key="workflow:execute",
        organization_id="org-1",
    )

    assert not repository.has_permission(
        user_id="user-2",
        permission_key="workflow:execute",
        organization_id="org-1",
    )


def test_rbac_repository_enforces_organization_scope() -> None:
    repository = make_repository()

    repository.create_role(
        role_id="role-reviewer",
        name="reviewer",
    )
    repository.create_permission(
        permission_id="permission-approval-read",
        resource="approval",
        action="read",
    )
    repository.assign_permission_to_role(
        role_id="role-reviewer",
        permission_id="permission-approval-read",
    )

    repository.create_membership(
        membership_id="membership-org-1",
        user_id="user-1",
        organization_id="org-1",
        role_id="role-reviewer",
    )

    assert repository.has_permission(
        user_id="user-1",
        permission_key="approval:read",
        organization_id="org-1",
    )

    assert not repository.has_permission(
        user_id="user-1",
        permission_key="approval:read",
        organization_id="org-2",
    )


def test_rbac_repository_combines_permissions_from_multiple_roles() -> None:
    repository = make_repository()

    repository.create_role(
        role_id="role-reader",
        name="reader",
    )
    repository.create_role(
        role_id="role-writer",
        name="writer",
    )

    repository.create_permission(
        permission_id="permission-read",
        resource="dataset",
        action="read",
    )
    repository.create_permission(
        permission_id="permission-write",
        resource="dataset",
        action="write",
    )

    repository.assign_permission_to_role(
        role_id="role-reader",
        permission_id="permission-read",
    )
    repository.assign_permission_to_role(
        role_id="role-writer",
        permission_id="permission-write",
    )

    repository.create_membership(
        membership_id="membership-reader",
        user_id="user-1",
        organization_id="org-1",
        role_id="role-reader",
    )
    repository.create_membership(
        membership_id="membership-writer",
        user_id="user-1",
        organization_id="org-1",
        role_id="role-writer",
    )

    permissions = repository.list_permission_keys(
        user_id="user-1",
        organization_id="org-1",
    )

    assert permissions == frozenset(
        {
            "dataset:read",
            "dataset:write",
        }
    )
