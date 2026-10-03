from unittest.mock import Mock, call

import pytest

from application.changesets.query_service import ChangeSetQueryService
from domain.identity import CurrentUser


def make_service():
    repository = Mock()
    return ChangeSetQueryService(changesets=repository), repository


def test_list_changesets_forwards_owner_and_preserves_results():
    service, repository = make_service()
    user = CurrentUser(user_id="owner-1")
    changesets = [object(), object()]
    repository.list_for_owner.return_value = changesets

    result = service.list_changesets(current_user=user)

    assert result is changesets
    repository.list_for_owner.assert_called_once_with(owner_id="owner-1")


def test_list_changesets_preserves_empty_result():
    service, repository = make_service()
    repository.list_for_owner.return_value = []

    result = service.list_changesets(
        current_user=CurrentUser(user_id="owner-1"),
    )

    assert result == []


@pytest.mark.parametrize("result", [object(), None])
def test_get_changeset_forwards_owner_and_preserves_result(result):
    service, repository = make_service()
    user = CurrentUser(user_id="owner-1")
    repository.get_for_owner.return_value = result

    actual = service.get_changeset(
        current_user=user,
        changeset_id="cs-1",
    )

    assert actual is result
    repository.get_for_owner.assert_called_once_with(
        changeset_id="cs-1",
        owner_id="owner-1",
    )


@pytest.mark.parametrize("result", [[object()], [], None])
def test_get_items_forwards_owner_and_preserves_result(result):
    service, repository = make_service()
    user = CurrentUser(user_id="owner-1")
    repository.list_items_for_owner.return_value = result

    actual = service.get_items(
        current_user=user,
        changeset_id="cs-1",
    )

    assert actual is result
    repository.list_items_for_owner.assert_called_once_with(
        changeset_id="cs-1",
        owner_id="owner-1",
    )


def test_repository_exception_propagates_unchanged():
    service, repository = make_service()
    error = RuntimeError("repository unavailable")
    repository.get_for_owner.side_effect = error

    with pytest.raises(RuntimeError) as raised:
        service.get_changeset(
            current_user=CurrentUser(user_id="owner-1"),
            changeset_id="cs-1",
        )

    assert raised.value is error
    assert repository.mock_calls == [
        call.get_for_owner(changeset_id="cs-1", owner_id="owner-1"),
    ]
