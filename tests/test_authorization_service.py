from domain.authorization import Permission
from domain.identity import CurrentUser
from services.authorization import AuthorizationService


def test_admin_can_execute_workflow():
    service = AuthorizationService()
    user = CurrentUser(
        user_id="user-1",
        roles=frozenset({"admin"}),
    )

    service.authorize(
        user=user,
        action="execute",
        resource="workflow",
    )


def test_data_engineer_can_execute_workflow():
    service = AuthorizationService()
    user = CurrentUser(
        user_id="user-1",
        roles=frozenset({"data_engineer"}),
    )

    service.authorize(
        user=user,
        action="execute",
        resource="workflow",
    )


def test_viewer_cannot_execute_workflow():
    service = AuthorizationService()
    user = CurrentUser(
        user_id="user-1",
        roles=frozenset({"viewer"}),
    )

    try:
        service.authorize(
            user=user,
            action="execute",
            resource="workflow",
        )
        assert False, "Expected PermissionError"
    except PermissionError:
        pass


def test_reviewer_can_decide_approval():
    service = AuthorizationService()
    user = CurrentUser(
        user_id="user-1",
        roles=frozenset({"reviewer"}),
    )

    service.authorize(
        user=user,
        action="decide",
        resource="approval",
    )


def test_unknown_role_is_denied():
    service = AuthorizationService()
    user = CurrentUser(
        user_id="user-1",
        roles=frozenset({"unknown-role"}),
    )

    decision = service.decide(
        user=user,
        permission=Permission(
            resource="workflow",
            action="read",
        ),
    )

    assert decision.allowed is False


def test_existing_authorization_contract_remains_usable():
    service = AuthorizationService()
    user = CurrentUser(
        user_id="user-1",
        roles=frozenset({"viewer"}),
    )

    service.authorize(
        user=user,
        action="read",
        resource="dataset",
    )
