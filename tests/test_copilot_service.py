import pytest
from application.copilot.contracts import (
    CopilotAction,
    CopilotApprovalEvent,
    CopilotResponse,
)
from application.copilot.service import CopilotService
from application.copilot.tools import CopilotToolRegistry
from domain.identity import CurrentUser


class FakeRequirements:
    def __init__(self):
        self.calls = []

    def interpret(self, **kwargs):
        self.calls.append(kwargs)

        from domain.requirement import WorkflowRequirement

        return WorkflowRequirement(
            requested_capabilities=("data.cleaning",),
            requested_intents=("clean",),
        )


class FakeProjects:
    def get_for_owner(self, *, project_id, owner_id):
        return object()


class FakePlanner:
    def __init__(self):
        self.calls = []

    def plan(self, requirement):
        self.calls.append(requirement)

        from domain.plans import ExecutionPlan, PlanStep

        return ExecutionPlan(
            steps=(
                PlanStep(
                    capability_id="data.cleaning",
                ),
            ),
            metadata={"source": "test"},
        )


def test_author_workflow_interprets_and_plans_without_execution():
    requirements = FakeRequirements()
    planner = FakePlanner()

    service = CopilotService(
        requirements=requirements,
        planner=planner,
        tools=CopilotToolRegistry(),
        projects=FakeProjects(),
    )

    user = CurrentUser(
        user_id="user-1",
        roles=frozenset(),
    )

    response = service.author_workflow(
        current_user=user,
        project_id="project-1",
        name="Product cleanup",
        user_request="clean the product dataset",
    )

    assert len(response.actions) == 1
    assert response.actions[0].action == "workflow_plan"

    arguments = response.actions[0].arguments

    assert arguments["project_id"] == "project-1"
    assert arguments["name"] == "Product cleanup"

    assert len(requirements.calls) == 1
    assert requirements.calls[0]["user_request"] == (
        "clean the product dataset"
    )
    assert requirements.calls[0]["user_id"] == "user-1"

    assert len(planner.calls) == 1
    assert planner.calls[0].requested_capabilities == (
        "data.cleaning",
    )


def test_invoke_tool_uses_registry_and_injects_current_user():
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class ExampleArguments:
        dataset_id: str

    calls = []

    def handler(*, current_user, arguments):
        calls.append((current_user, arguments))
        return "ok"

    from application.copilot.tools import CopilotTool

    registry = CopilotToolRegistry(
        tools=(
            CopilotTool(
                name="get_dataset",
                description="Read dataset",
                handler=handler,
                arguments_type=ExampleArguments,
            ),
        )
    )

    service = CopilotService(
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        tools=registry,
        projects=FakeProjects(),
    )

    user = CurrentUser(
        user_id="user-42",
        roles=frozenset({"operator"}),
    )

    result = service.invoke_tool(
        current_user=user,
        tool_name="get_dataset",
        arguments={"dataset_id": "dataset-1"},
    )

    assert result == "ok"
    assert calls == [
        (
            user,
            ExampleArguments(dataset_id="dataset-1"),
        )
    ]


def test_author_workflow_rejects_project_outside_owner_scope():
    class EmptyProjects:
        def get_for_owner(self, *, project_id, owner_id):
            return None

    service = CopilotService(
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        tools=CopilotToolRegistry(),
        projects=EmptyProjects(),
    )

    with pytest.raises(ValueError, match="Project not found"):
        service.author_workflow(
            current_user=CurrentUser(user_id="user-1"),
            project_id="project-forbidden",
            name="Cleanup",
            user_request="clean product data",
        )
def test_invoke_tool_rejects_unknown_tool():
    service = CopilotService(
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        tools=CopilotToolRegistry(),
        projects=FakeProjects(),
    )

    user = CurrentUser(
        user_id="user-42",
        roles=frozenset({"operator"}),
    )

    with pytest.raises(ValueError, match="Unknown Copilot tool"):
        service.invoke_tool(
            current_user=user,
            tool_name="delete_everything",
            arguments={},
        )


def test_invoke_tool_rejects_non_object_arguments():
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class ExampleArguments:
        dataset_id: str

    calls = []

    def handler(*, current_user, arguments):
        calls.append((current_user, arguments))
        return "should not run"

    from application.copilot.tools import CopilotTool

    registry = CopilotToolRegistry(
        tools=(
            CopilotTool(
                name="get_dataset",
                description="Read dataset",
                handler=handler,
                arguments_type=ExampleArguments,
            ),
        )
    )

    service = CopilotService(
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        tools=registry,
        projects=FakeProjects(),
    )

    user = CurrentUser(
        user_id="user-42",
        roles=frozenset({"operator"}),
    )

    with pytest.raises(TypeError, match="arguments must be an object"):
        service.invoke_tool(
            current_user=user,
            tool_name="get_dataset",
            arguments="not-an-object",
        )

    assert calls == []

def test_respond_delegates_to_copilot_agent_without_tool_action():
    expected = CopilotResponse(
        message="I found a dataset issue.",
    )

    class FakeAgent:
        def __init__(self):
            self.calls = []

        def respond(self, user_message):
            self.calls.append(user_message)
            return expected

    agent = FakeAgent()
    service = CopilotService(
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        tools=CopilotToolRegistry(),
        projects=FakeProjects(),
        agent=agent,
    )

    user = CurrentUser(
        user_id="user-1",
        roles=frozenset(),
    )

    result = service.respond(
        current_user=user,
        user_message="what did you find?",
    )

    assert result is expected
    assert agent.calls == ["what did you find?"]

def test_respond_rejects_unregistered_tool_action():
    expected = CopilotResponse(
        message="I found a dataset issue.",
        actions=(
            CopilotAction(
                action="get_health",
                arguments={"dataset_id": "ds-1"},
            ),
        ),
    )

    class FakeAgent:
        def respond(self, user_message):
            return expected

    service = CopilotService(
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        tools=CopilotToolRegistry(),
        projects=FakeProjects(),
        agent=FakeAgent(),
    )

    user = CurrentUser(
        user_id="user-1",
        roles=frozenset(),
    )

    with pytest.raises(ValueError, match="Unknown Copilot tool"):
        service.respond(
            current_user=user,
            user_message="check dataset health",
        )

def test_stream_dispatches_tool_and_continues_agent():
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class HealthArguments:
        dataset_id: str

    calls = []

    def get_health_handler(*, current_user, arguments):
        calls.append((current_user, arguments))
        return {"status": "healthy"}

    from application.copilot.tools import CopilotTool

    registry = CopilotToolRegistry(
        tools=(
            CopilotTool(
                name="get_health",
                description="Read dataset health",
                handler=get_health_handler,
                arguments_type=HealthArguments,
            ),
        )
    )

    action = CopilotAction(
        action="get_health",
        arguments={"dataset_id": "ds-1"},
        call_id="call-1",
    )

    final_response = CopilotResponse(
        message="Dataset is healthy.",
    )

    class FakeAgent:
        def __init__(self):
            self.stream_calls = []
            self.continuation_calls = []

        def stream(self, user_message, *, history=None):
            self.stream_calls.append(user_message)
            yield action

        def respond_with_tool_result(
            self,
            *,
            user_message,
            action,
            tool_result,
            history=None,
        ):
            self.continuation_calls.append(
                (user_message, action, tool_result)
            )
            return final_response
    agent = FakeAgent()

    service = CopilotService(
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        tools=registry,
        projects=FakeProjects(),
        agent=agent,
    )

    user = CurrentUser(
        user_id="user-42",
        roles=frozenset({"operator"}),
    )

    result = list(
        service.stream(
            current_user=user,
            user_message="check dataset health",
        )
    )

    assert result == ["Dataset is healthy."]
    assert agent.stream_calls == ["check dataset health"]

    assert calls == [
        (
            user,
            HealthArguments(dataset_id="ds-1"),
        )
    ]

    assert len(agent.continuation_calls) == 1

    continuation_message, continuation_action, continuation_result = (
        agent.continuation_calls[0]
    )

    assert continuation_message == "check dataset health"
    assert continuation_action == action
    assert continuation_result == {"status": "healthy"}

def test_stream_delegates_to_copilot_agent():
    class FakeAgent:
        def __init__(self):
            self.calls = []

        def stream(self, user_message, *, history=None):
            self.calls.append(user_message)
            yield "Hello "
            yield "from Copilot."

    agent = FakeAgent()
    service = CopilotService(
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        tools=CopilotToolRegistry(),
        projects=FakeProjects(),
        agent=agent,
    )

    user = CurrentUser(
        user_id="user-1",
        roles=frozenset(),
    )

    result = list(
        service.stream(
            current_user=user,
            user_message="hello",
        )
    )

    assert result == ["Hello ", "from Copilot."]
    assert agent.calls == ["hello"]






def test_create_session_returns_owned_session():
    service = CopilotService(
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        tools=CopilotToolRegistry(),
        projects=FakeProjects(),
    )

    user = CurrentUser(
        user_id="user-1",
        roles=frozenset(),
    )

    session = service.create_session(current_user=user)

    assert session.session_id
    assert session.owner_id == "user-1"


def test_get_session_returns_existing_owned_session():
    service = CopilotService(
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        tools=CopilotToolRegistry(),
        projects=FakeProjects(),
    )

    user = CurrentUser(
        user_id="user-1",
        roles=frozenset(),
    )

    created = service.create_session(current_user=user)
    loaded = service.get_session(
        current_user=user,
        session_id=created.session_id,
    )

    assert loaded is created


def test_get_session_rejects_session_owned_by_another_user():
    service = CopilotService(
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        tools=CopilotToolRegistry(),
        projects=FakeProjects(),
    )

    owner = CurrentUser(user_id="owner-1")
    other_user = CurrentUser(user_id="other-1")

    created = service.create_session(current_user=owner)

    with pytest.raises(ValueError, match="Copilot session not found"):
        service.get_session(
            current_user=other_user,
            session_id=created.session_id,
        )

def test_session_stores_conversation_turns():
    service = CopilotService(
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        tools=CopilotToolRegistry(),
        projects=FakeProjects(),
    )

    user = CurrentUser(user_id="user-1")
    session = service.create_session(current_user=user)

    service.append_session_turn(
        current_user=user,
        session_id=session.session_id,
        role="user",
        content="check dataset health",
    )

    loaded = service.get_session(
        current_user=user,
        session_id=session.session_id,
    )

    assert loaded.turns == (
        ("user", "check dataset health"),
    )

def test_session_stores_tool_call_and_result():
    service = CopilotService(
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        tools=CopilotToolRegistry(),
        projects=FakeProjects(),
    )

    user = CurrentUser(user_id="user-1")
    session = service.create_session(current_user=user)

    service.append_session_turn(
        current_user=user,
        session_id=session.session_id,
        role="user",
        content="check dataset health",
    )

    service.append_session_action(
        current_user=user,
        session_id=session.session_id,
        action=CopilotAction(
            action="get_health",
            arguments={"dataset_id": "ds-1"},
            call_id="call-1",
        ),
    )

    service.append_session_tool_result(
        current_user=user,
        session_id=session.session_id,
        action=CopilotAction(
            action="get_health",
            arguments={"dataset_id": "ds-1"},
            call_id="call-1",
        ),
        result={"status": "healthy"},
    )

    loaded = service.get_session(
        current_user=user,
        session_id=session.session_id,
    )

    assert loaded.turns[0] == (
        "user",
        "check dataset health",
    )
    assert loaded.events[1].kind == "tool_call"
    assert loaded.events[1].action.action == "get_health"
    assert loaded.events[1].action.call_id == "call-1"
    assert loaded.events[2].kind == "tool_result"
    assert loaded.events[2].result == {"status": "healthy"}

def test_stream_passes_session_history_to_agent():
    from dataclasses import dataclass

    from application.copilot.tools import CopilotTool

    @dataclass(frozen=True)
    class HealthArguments:
        dataset_id: str

    def get_health_handler(*, current_user, arguments):
        return {"status": "healthy"}

    registry = CopilotToolRegistry(
        tools=(
            CopilotTool(
                name="get_health",
                description="Read dataset health",
                handler=get_health_handler,
                arguments_type=HealthArguments,
            ),
        )
    )

    action = CopilotAction(
        action="get_health",
        arguments={"dataset_id": "ds-1"},
        call_id="call-1",
    )

    class HistoryAwareAgent:
        def __init__(self):
            self.stream_history = None
            self.continuation_history = None

        def stream(self, user_message, *, history=None):
            self.stream_history = history
            yield action

        def respond_with_tool_result(
            self,
            *,
            user_message,
            action,
            tool_result,
            history=None,
        ):
            self.continuation_history = history
            return CopilotResponse(message="Dataset is healthy.")

    agent = HistoryAwareAgent()

    service = CopilotService(
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        tools=registry,
        projects=FakeProjects(),
        agent=agent,
    )

    user = CurrentUser(user_id="user-42")
    session = service.create_session(current_user=user)

    service.append_session_turn(
        current_user=user,
        session_id=session.session_id,
        role="user",
        content="previous question",
    )

    list(
        service.stream(
            current_user=user,
            user_message="check dataset health",
            session_id=session.session_id,
        )
    )

    assert agent.stream_history is not None
    assert agent.stream_history[0].role == "user"
    assert agent.stream_history[0].content == "previous question"
    assert len(agent.stream_history) == 1

    assert agent.continuation_history is not None
    assert agent.continuation_history[0].role == "user"
    assert agent.continuation_history[0].content == "previous question"
    assert agent.continuation_history == agent.stream_history


def test_stream_records_conversation_events_in_session():
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class HealthArguments:
        dataset_id: str

    def get_health_handler(*, current_user, arguments):
        return {"status": "healthy"}

    from application.copilot.tools import CopilotTool

    registry = CopilotToolRegistry(
        tools=(
            CopilotTool(
                name="get_health",
                description="Read dataset health",
                handler=get_health_handler,
                arguments_type=HealthArguments,
            ),
        )
    )

    action = CopilotAction(
        action="get_health",
        arguments={"dataset_id": "ds-1"},
        call_id="call-1",
    )

    class FakeAgent:
        def stream(self, user_message, *, history=None):
            yield action

        def respond_with_tool_result(
            self,
            *,
            user_message,
            action,
            tool_result,
            history=None,
        ):
            return CopilotResponse(
                message="Dataset is healthy.",
            )

    service = CopilotService(
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        tools=registry,
        projects=FakeProjects(),
        agent=FakeAgent(),
    )

    user = CurrentUser(user_id="user-42")
    session = service.create_session(current_user=user)

    result = list(
        service.stream(
            current_user=user,
            user_message="check dataset health",
            session_id=session.session_id,
        )
    )

    assert result == ["Dataset is healthy."]

    loaded = service.get_session(
        current_user=user,
        session_id=session.session_id,
    )

    assert [event.kind for event in loaded.events] == [
        "text",
        "tool_call",
        "tool_result",
        "text",
    ]

    assert loaded.events[0].role == "user"
    assert loaded.events[0].content == "check dataset health"

    assert loaded.events[1].action == action

    assert loaded.events[2].action == action
    assert loaded.events[2].result == {"status": "healthy"}

    assert loaded.events[3].role == "assistant"
    assert loaded.events[3].content == "Dataset is healthy."


def test_stream_exposes_safe_pending_approval_event():
    from dataclasses import dataclass
    from application.copilot.tools import CopilotTool

    @dataclass(frozen=True)
    class ExecuteArguments:
        workflow_id: str

    approval = {
        "approval_id": "approval-1",
        "execution_id": "execution-1",
        "changeset_id": "changeset-1",
        "risk_score": "HIGH",
        "confidence_score": 0.85,
        "requested_by": "user-42",
        "created_at": "2026-09-18T10:00:00+00:00",
        "expires_at": None,
        "status": "PENDING",
    }

    def execute_handler(*, current_user, arguments):
        return {
            "execution_id": "execution-1",
            "status": "PENDING_APPROVAL",
            "changeset_id": "changeset-1",
            "approval": approval,
        }

    registry = CopilotToolRegistry(
        tools=(
            CopilotTool(
                name="execute_workflow",
                description="Execute governed workflow",
                handler=execute_handler,
                arguments_type=ExecuteArguments,
            ),
        )
    )

    action = CopilotAction(
        action="execute_workflow",
        arguments={"workflow_id": "workflow-1"},
    )

    class FakeAgent:
        def stream(self, user_message, *, history=None):
            yield action

        def respond_with_tool_result(
            self,
            *,
            user_message,
            action,
            tool_result,
            history=None,
        ):
            return CopilotResponse(message="Waiting for approval.")

    service = CopilotService(
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        tools=registry,
        projects=FakeProjects(),
        agent=FakeAgent(),
    )

    events = list(
        service.stream(
            current_user=CurrentUser(user_id="user-42"),
            user_message="execute workflow",
        )
    )

    assert isinstance(events[0], CopilotApprovalEvent)
    assert events[0].approval == approval
    assert "token" not in events[0].approval
    assert "token_hash" not in events[0].approval
    assert events[1] == "Waiting for approval."


