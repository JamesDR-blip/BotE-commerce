import httpx
import pytest

from app.api_client import DashboardApiClient, DashboardApiError


def _client(handler) -> DashboardApiClient:
    return DashboardApiClient("http://api.test", httpx.Client(transport=httpx.MockTransport(handler), base_url="http://api.test"))


def test_dashboard_client_calls_fastapi_endpoints() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/categories":
            return httpx.Response(200, json={"categories": ["Fashion"]})
        if request.url.path == "/validate":
            return httpx.Response(200, json={"execution_id": "id", "category": "Fashion", "health_score": 90, "reports": {"json": "/report/id/json"}, "cached": False})
        if request.url.path == "/history":
            return httpx.Response(200, json={"items": [{"id": "id", "category": "Fashion", "health_score": 90, "created_at": "2026-01-01T00:00:00Z"}]})
        return httpx.Response(200, content=b"report")

    client = _client(handler)
    assert client.categories() == ["Fashion"]
    assert client.validate("items.csv", b"Size\nM\n", "text/csv", "Fashion").health_score == 90
    assert client.history()[0]["id"] == "id"
    assert client.download_report("/report/id/json") == b"report"


def test_dashboard_client_exposes_backend_error_detail() -> None:
    client = _client(lambda request: httpx.Response(422, json={"detail": "Unsupported category"}))
    with pytest.raises(DashboardApiError, match="Unsupported category"):
        client.categories()
