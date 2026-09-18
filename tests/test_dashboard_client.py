import httpx
import pytest

from app.api_client import CopilotEvent, DashboardApiClient, DashboardApiError


def _client(handler) -> DashboardApiClient:
    return DashboardApiClient(
        "http://api.test",
        httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="http://api.test",
        ),
    )


def test_dashboard_client_calls_fastapi_endpoints() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/categories":
            return httpx.Response(200, json={"categories": ["Fashion"]})
        if request.url.path == "/validate":
            return httpx.Response(
                200,
                json={
                    "execution_id": "id",
                    "category": "Fashion",
                    "health_score": 90,
                    "reports": {"json": "/report/id/json"},
                    "cached": False,
                },
            )
        if request.url.path == "/history":
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "id": "id",
                            "category": "Fashion",
                            "health_score": 90,
                            "created_at": "2026-01-01T00:00:00Z",
                        }
                    ]
                },
            )
        return httpx.Response(200, content=b"report")

    client = _client(handler)
    assert client.categories() == ["Fashion"]
    assert client.validate(
        "items.csv",
        b"Size\nM\n",
        "text/csv",
        "Fashion",
    ).health_score == 90
    assert client.history()[0]["id"] == "id"
    assert client.download_report("/report/id/json") == b"report"


def test_dashboard_client_exposes_backend_error_detail() -> None:
    client = _client(
        lambda request: httpx.Response(
            422,
            json={"detail": "Unsupported category"},
        )
    )
    with pytest.raises(DashboardApiError, match="Unsupported category"):
        client.categories()


def test_dashboard_client_loads_s15_health_endpoints() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/workspaces/workspace-1/projects":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "project-1",
                        "workspace_id": "workspace-1",
                        "name": "Products",
                        "description": "Product data",
                    }
                ],
            )

        if request.url.path == "/health-metrics":
            assert request.url.params["project_id"] == "project-1"
            return httpx.Response(
                200,
                json={
                    "project_id": "project-1",
                    "items": [
                        {
                            "dataset_id": "dataset-1",
                            "dataset_name": "Products",
                            "aggregate": 91.25,
                            "metrics": [
                                {
                                    "dimension": "completeness",
                                    "score": 95.0,
                                    "assessed": True,
                                },
                                {
                                    "dimension": "timeliness",
                                    "score": 0.0,
                                    "assessed": False,
                                },
                            ],
                        }
                    ],
                },
            )

        if request.url.path == "/diagnostics/dataset-1":
            return httpx.Response(
                200,
                json={
                    "dataset_id": "dataset-1",
                    "diagnostics": [
                        {
                            "code": "invalid_price",
                            "field": "price",
                            "message": "Price must be positive.",
                            "severity": "error",
                            "count": 2,
                        }
                    ],
                    "remediation_proposals": [
                        {
                            "id": "proposal-1",
                            "diagnostic_code": "invalid_price",
                            "action": "review_invalid_price_issues",
                            "rationale": "Price must be positive.",
                            "severity": "error",
                            "status": "PROPOSED",
                        }
                    ],
                },
            )

        return httpx.Response(404, json={"detail": "Not found"})

    client = _client(handler)

    projects = client.projects("workspace-1")
    assert projects[0].id == "project-1"

    health = client.health_metrics("project-1")
    assert health.items[0].aggregate == 91.25
    assert health.items[0].metrics[0].dimension == "completeness"

    diagnostics = client.diagnostics("dataset-1")
    assert diagnostics.diagnostics[0].code == "invalid_price"
    assert diagnostics.remediation_proposals[0].status == "PROPOSED"


def test_dashboard_client_creates_copilot_session() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/copilot/sessions"
        return httpx.Response(200, json={"session_id": "session-1"})

    client = _client(handler)

    session = client.create_copilot_session()

    assert session.session_id == "session-1"


def test_dashboard_client_streams_copilot_text_events() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/copilot/chat"
        assert request.read() == b'{"message":"hello","session_id":"session-1"}'
        return httpx.Response(
            200,
            text="""\
: heartbeat

data: {"type":"text","content":"Hello"}

data: {"type":"text","content":" world"}

""",
            headers={"content-type": "text/event-stream"},
        )

    client = _client(handler)

    events = list(
        client.stream_copilot(
            "hello",
            session_id="session-1",
        )
    )

    assert events == [
        CopilotEvent(type="text", content="Hello"),
        CopilotEvent(type="text", content=" world"),
    ]


def test_dashboard_client_streams_copilot_action_events() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="""\
data: {"type":"action","action":"get_health","arguments":{"dataset_id":"dataset-1"}}

""",
            headers={"content-type": "text/event-stream"},
        )

    client = _client(handler)

    events = list(client.stream_copilot("check health"))

    assert events == [
        CopilotEvent(
            type="action",
            action="get_health",
            arguments={"dataset_id": "dataset-1"},
        )
    ]


def test_dashboard_client_copilot_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"detail": "Authentication required"},
        )

    client = _client(handler)

    with pytest.raises(DashboardApiError, match="Authentication required"):
        list(client.stream_copilot("hello"))


def test_dashboard_client_ignores_malformed_and_non_data_sse_lines() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="""\
: comment
event: ignored
data: not-json
data: {"type":"text","content":"ok"}

""",
            headers={"content-type": "text/event-stream"},
        )

    client = _client(handler)

    events = list(client.stream_copilot("hello"))

    assert events == [
        CopilotEvent(type="text", content="ok"),
    ]


def test_dashboard_client_streams_copilot_approval_events() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="""data: {"type":"approval","approval":{"approval_id":"approval-1","execution_id":"execution-1","changeset_id":"changeset-1","risk_score":"HIGH","confidence_score":0.85,"requested_by":"owner-1","created_at":"2026-09-18T10:00:00+00:00","expires_at":null,"status":"PENDING"}}

""",
            headers={"content-type": "text/event-stream"},
        )

    client = _client(handler)

    events = list(client.stream_copilot("execute workflow"))

    assert events == [
        CopilotEvent(
            type="approval",
            approval={
                "approval_id": "approval-1",
                "execution_id": "execution-1",
                "changeset_id": "changeset-1",
                "risk_score": "HIGH",
                "confidence_score": 0.85,
                "requested_by": "owner-1",
                "created_at": "2026-09-18T10:00:00+00:00",
                "expires_at": None,
                "status": "PENDING",
            },
        )
    ]
