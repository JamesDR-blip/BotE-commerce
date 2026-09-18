from fastapi.testclient import TestClient

from api.dependencies import get_copilot_service, get_current_user
from api.main import create_app
from configs.settings import Settings
from domain.identity import CurrentUser
from domain.plans import ExecutionPlan, PlanStep
from domain.requirement import WorkflowRequirement
from application.copilot.contracts import (
    CopilotAction,
    CopilotApprovalEvent,
    CopilotResponse,
)


def _client():
    app = create_app(Settings(database_url="sqlite://"))
    app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="owner-1")
    )
    return app, TestClient(app)


class FakeCopilot:
    def author_workflow(
        self,
        *,
        current_user,
        project_id,
        name,
        user_request,
    ):
        assert current_user.user_id == "owner-1"
        assert project_id == "project-1"
        assert name == "Product cleanup"
        assert user_request == "clean product data"

        requirement = WorkflowRequirement(
            requested_capabilities=("data.cleaning",),
            requested_intents=("clean",),
            parameters={"data.cleaning": {"mode": "safe"}},
        )
        plan = ExecutionPlan(
            steps=(
                PlanStep(
                    capability_id="data.cleaning",
                    capability_version="1.0",
                    parameters={"mode": "safe"},
                    input_mapping={},
                ),
            ),
            metadata={"source": "copilot"},
        )
        return CopilotResponse(
            message="Workflow plan authored successfully.",
            actions=(
                CopilotAction(
                    action="workflow_plan",
                    arguments={
                        "project_id": project_id,
                        "name": name,
                        "requirement": requirement,
                        "plan": plan,
                    },
                ),
            ),
        )


def test_author_workflow_endpoint_returns_json_safe_plan():
    app, client = _client()
    app.dependency_overrides[get_copilot_service] = lambda: FakeCopilot()

    response = client.post(
        "/copilot/author-workflow",
        json={
            "project_id": "project-1",
            "name": "Product cleanup",
            "user_request": "clean product data",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["project_id"] == "project-1"
    assert payload["name"] == "Product cleanup"
    assert payload["requested_capabilities"] == ["data.cleaning"]
    assert payload["requested_intents"] == ["clean"]
    assert payload["parameters"]["data.cleaning"]["mode"] == "safe"
    assert payload["plan"]["steps"][0]["capability_id"] == "data.cleaning"
    assert payload["plan"]["metadata"]["source"] == "copilot"


def test_author_workflow_endpoint_requires_authentication():
    app = create_app(Settings(database_url="sqlite://"))
    client = TestClient(app)

    response = client.post(
        "/copilot/author-workflow",
        json={
            "project_id": "project-1",
            "name": "Product cleanup",
            "user_request": "clean product data",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_author_workflow_endpoint_maps_project_scope_failure_to_404():
    class ScopeFailureCopilot:
        def author_workflow(self, **kwargs):
            raise ValueError("Project not found: project-forbidden")

    app, client = _client()
    app.dependency_overrides[get_copilot_service] = (
        lambda: ScopeFailureCopilot()
    )

    response = client.post(
        "/copilot/author-workflow",
        json={
            "project_id": "project-forbidden",
            "name": "Cleanup",
            "user_request": "clean product data",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found: project-forbidden"


def test_author_workflow_endpoint_rejects_empty_user_request():
    app, client = _client()
    app.dependency_overrides[get_copilot_service] = lambda: FakeCopilot()

    response = client.post(
        "/copilot/author-workflow",
        json={
            "project_id": "project-1",
            "name": "Product cleanup",
            "user_request": "",
        },
    )

    assert response.status_code == 422

def test_chat_stream_returns_sse_action_events():
    class StreamCopilot:
        def stream(self, *, current_user, user_message, session_id=None):
            assert current_user.user_id == "owner-1"
            assert user_message == "check health"
            assert session_id is None
            yield CopilotAction(
                action="get_health",
                arguments={"dataset_id": "ds-1"},
            )

    app, client = _client()

    app.dependency_overrides[get_copilot_service] = (
        lambda: StreamCopilot()
    )

    response = client.post(
        "/copilot/chat",
        json={"message": "check health"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text == (
        'data: {"type": "action", "action": "get_health", "arguments": {"dataset_id": "ds-1"}}\n\n'
    )

def test_chat_stream_passes_session_id_to_copilot():
    class StreamCopilot:
        def stream(self, *, current_user, user_message, session_id=None):
            assert current_user.user_id == "owner-1"
            assert user_message == "continue conversation"
            assert session_id == "session-123"
            yield "Conversation continued."

    app, client = _client()

    app.dependency_overrides[get_copilot_service] = (
        lambda: StreamCopilot()
    )

    response = client.post(
        "/copilot/chat",
        json={
            "message": "continue conversation",
            "session_id": "session-123",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text == (
        'data: {"type": "text", "content": "Conversation continued."}\n\n'
    )


def test_chat_stream_returns_sse_text_events():
    class StreamCopilot:
        def stream(self, *, current_user, user_message, session_id=None):
            assert current_user.user_id == "owner-1"
            assert user_message == "hello"
            assert session_id is None
            yield "Hello "
            yield "from Copilot."

    app, client = _client()

    app.dependency_overrides[get_copilot_service] = (
        lambda: StreamCopilot()
    )

    response = client.post(
        "/copilot/chat",
        json={"message": "hello"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text == (
        'data: {"type": "text", "content": "Hello "}\n\n'
        'data: {"type": "text", "content": "from Copilot."}\n\n'
    )

def test_chat_stream_returns_final_text_after_tool_dispatch():
    class StreamCopilot:
        def stream(self, *, current_user, user_message, session_id=None):
            assert current_user.user_id == "owner-1"
            assert user_message == "check health"
            assert session_id is None
            yield "Dataset is healthy."

    app, client = _client()

    app.dependency_overrides[get_copilot_service] = (
        lambda: StreamCopilot()
    )

    response = client.post(
        "/copilot/chat",
        json={"message": "check health"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text == (
        'data: {"type": "text", "content": "Dataset is healthy."}\n\n'
    )

def test_create_copilot_session_returns_session_id():
    class SessionCopilot:
        def create_session(self, *, current_user):
            assert current_user.user_id == "owner-1"

            class Session:
                session_id = "session-123"

            return Session()

    app, client = _client()
    app.dependency_overrides[get_copilot_service] = (
        lambda: SessionCopilot()
    )

    response = client.post("/copilot/sessions")

    assert response.status_code == 200
    assert response.json() == {
        "session_id": "session-123",
    }


def test_create_copilot_session_requires_authentication():
    app = create_app(Settings(database_url="sqlite://"))
    client = TestClient(app)

    response = client.post("/copilot/sessions")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_chat_stream_returns_sse_approval_event_without_credentials():
    class StreamCopilot:
        def stream(self, *, current_user, user_message, session_id=None):
            yield CopilotApprovalEvent(
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

    app, client = _client()
    app.dependency_overrides[get_copilot_service] = (
        lambda: StreamCopilot()
    )

    response = client.post(
        "/copilot/chat",
        json={"message": "execute workflow"},
    )

    assert response.status_code == 200
    assert response.text == (
        'data: {"type": "approval", "approval": {"approval_id": "approval-1", '
        '"execution_id": "execution-1", "changeset_id": "changeset-1", '
        '"risk_score": "HIGH", "confidence_score": 0.85, '
        '"requested_by": "owner-1", "created_at": "2026-09-18T10:00:00+00:00", '
        '"expires_at": null, "status": "PENDING"}}\n\n'
    )
    assert "token" not in response.text
    assert "token_hash" not in response.text
