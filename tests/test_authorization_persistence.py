from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from domain.authorization import Permission
from domain.identity import CurrentUser
from repositories.rbac import RBACRepository
from services.authorization import AuthorizationService


def make_service() -> AuthorizationService:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    repository = RBACRepository(sessions)
    return AuthorizationService(repository)


def test_persisted_role_grants_permission() -> None:
    service = make_service()
    repository = service.rbac_repository

    repository.create_role(
        role_id="role-engineer",
        name="data_engineer",
    )
    repository.create_permission(
        permission_id="permission-execute",
        resource="workflow",
        action="execute",
    )
    repository.assign_permission_to_role(
        role_id="role-engineer",
        permission_id="permission-execute",
    )
    repository.create_membership(
        membership_id="membership-1",
        user_id="user-1",
        organization_id="org-1",
        role_id="role-engineer",
    )

    service.authorize(
        user=CurrentUser(user_id="user-1"),
        resource="workflow",
        action="execute",
        organization_id="org-1",
    )


def test_persisted_rbac_denies_user_without_membership() -> None:
    service = make_service()

    decision = service.decide(
        user=CurrentUser(
            user_id="user-1",
            roles=frozenset({"admin"}),
        ),
        permission=Permission(
            resource="workflow",
            action="execute",
        ),
        organization_id="org-1",
    )

    assert decision.allowed is False


def test_persisted_rbac_denies_wrong_organization() -> None:
    service = make_service()
    repository = service.rbac_repository

    repository.create_role(
        role_id="role-reviewer",
        name="reviewer",
    )
    repository.create_permission(
        permission_id="permission-approval",
        resource="approval",
        action="decide",
    )
    repository.assign_permission_to_role(
        role_id="role-reviewer",
        permission_id="permission-approval",
    )
    repository.create_membership(
        membership_id="membership-1",
        user_id="user-1",
        organization_id="org-1",
        role_id="role-reviewer",
    )

    decision = service.decide(
        user=CurrentUser(user_id="user-1"),
        permission=Permission(
            resource="approval",
            action="decide",
        ),
        organization_id="org-2",
    )

    assert decision.allowed is False


def test_legacy_authorization_without_repository_remains_usable() -> None:
    service = AuthorizationService()

    service.authorize(
        user=CurrentUser(
            user_id="user-1",
            roles=frozenset({"admin"}),
        ),
        resource="workflow",
        action="execute",
    )
