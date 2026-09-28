from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from hypothesis import given, settings, strategies as st

from api.dependencies import get_current_user
from api.main import create_app
from configs.settings import Settings
from domain.identity import CurrentUser


def make_client() -> TestClient:
    app = create_app(Settings(database_url="sqlite://"))
    app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="fuzz-user")
    )
    return TestClient(app)


JSON_SCALARS = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(max_size=100),
)


@settings(deadline=None)
@given(
    st.sampled_from(
        [
            "approval_id",
            "execution_id",
            "changeset_id",
            "risk_score",
            "confidence_score",
        ]
    )
)
def test_approval_request_rejects_generated_missing_required_fields(
    missing_field: str,
) -> None:
    payload: dict[str, Any] = {
        "approval_id": "approval-1",
        "execution_id": "execution-1",
        "changeset_id": "changeset-1",
        "risk_score": "HIGH",
        "confidence_score": 0.85,
    }
    payload.pop(missing_field)

    response = make_client().post(
        "/approval/request",
        json=payload,
    )

    assert response.status_code == 422


@given(
    st.one_of(
        st.none(),
        st.lists(JSON_SCALARS, max_size=5),
        st.dictionaries(st.text(max_size=20), JSON_SCALARS, max_size=5),
    )
)
def test_approval_request_rejects_generated_invalid_confidence_score(
    invalid_value: Any,
) -> None:
    payload = {
        "approval_id": "approval-1",
        "execution_id": "execution-1",
        "changeset_id": "changeset-1",
        "risk_score": "HIGH",
        "confidence_score": invalid_value,
    }

    response = make_client().post(
        "/approval/request",
        json=payload,
    )

    assert response.status_code == 422


@given(
    st.dictionaries(
        st.text(max_size=20),
        JSON_SCALARS,
        max_size=8,
    )
)
def test_approval_token_endpoint_rejects_generated_bodies_without_token(
    payload: dict[str, Any],
) -> None:
    payload.pop("token", None)

    response = make_client().post(
        "/approvals/approval-1/approve",
        json=payload,
    )

    assert response.status_code == 422
