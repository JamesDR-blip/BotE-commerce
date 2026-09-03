from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from api.dependencies import get_current_user
from domain.identity import CurrentUser
from services.authentication import AuthenticationService


class StubAuthenticationService(AuthenticationService):
    def authenticate(self, token: str) -> CurrentUser:
        return CurrentUser(
            user_id=f"user:{token}",
            roles=frozenset({"user"}),
        )


def build_client() -> TestClient:
    app = FastAPI()

    authentication = StubAuthenticationService()

    @app.get("/protected")
    def protected(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> dict:
        return {
            "user_id": current_user.user_id,
            "roles": sorted(current_user.roles),
        }

    app.state.authentication = authentication

    return TestClient(app)


def test_missing_authorization_returns_401():
    client = build_client()

    response = client.get("/protected")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_invalid_authorization_scheme_returns_401():
    client = build_client()

    response = client.get(
        "/protected",
        headers={"Authorization": "Basic abc"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid authentication credentials"
    )


def test_bearer_token_returns_current_user():
    client = build_client()

    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer abc123"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "user_id": "user:abc123",
        "roles": ["user"],
    }