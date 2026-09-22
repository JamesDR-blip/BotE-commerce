from domain.authorization import (
    AuthorizationDecision,
    Membership,
    Organization,
    Permission,
    RoleName,
)
from domain.organization import OrganizationResource


def test_permission_key():
    permission = Permission(
        resource="workflow",
        action="execute",
    )

    assert permission.key == "workflow:execute"


def test_permission_rejects_empty_values():
    try:
        Permission(resource="", action="execute")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_organization_requires_identity():
    organization = Organization(
        id="org-1",
        name="Acme",
    )

    assert organization.id == "org-1"
    assert organization.name == "Acme"


def test_membership_binds_user_to_organization_and_role():
    membership = Membership(
        user_id="user-1",
        organization_id="org-1",
        role=RoleName.DATA_ENGINEER,
    )

    assert membership.user_id == "user-1"
    assert membership.organization_id == "org-1"
    assert membership.role == RoleName.DATA_ENGINEER


def test_authorization_decision():
    allowed = AuthorizationDecision.allow()
    denied = AuthorizationDecision.deny("Missing permission")

    assert allowed.allowed is True
    assert denied.allowed is False
    assert denied.reason == "Missing permission"


def test_organization_resource():
    resource = OrganizationResource(
        resource_id="workflow-1",
        organization_id="org-1",
    )

    assert resource.resource_id == "workflow-1"
    assert resource.organization_id == "org-1"
