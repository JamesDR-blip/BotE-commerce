from types import SimpleNamespace

import pytest

from application.copilot.agent import CopilotAgent
from application.copilot.contracts import CopilotAction


class FakeModel:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def test_text_response_returns_message():
    response = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[SimpleNamespace(text="Hello from Copilot.", functionCall=None)]
                )
            )
        ]
    )

    model = FakeModel(response)
    agent = CopilotAgent(
        model=model,
        model_name="test-model",
        tool_registry=None,
    )

    result = agent.respond("hello")

    assert result.message == "Hello from Copilot."
    assert result.actions == ()
    assert model.calls[0]["model"] == "test-model"


def test_registered_function_call_returns_action():
    response = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[
                        SimpleNamespace(
                            text=None,
                            functionCall=SimpleNamespace(
                                name="get_health",
                                args={"dataset_id": "ds-1"},
                            ),
                        )
                    ]
                )
            )
        ]
    )

    registry = SimpleNamespace(
        names=lambda: ("get_health",),
        to_function_declarations=lambda: (),
    )
    model = FakeModel(response)

    agent = CopilotAgent(
        model=model,
        model_name="test-model",
        tool_registry=registry,
    )

    result = agent.respond("check dataset health")

    assert result.message == ""
    assert len(result.actions) == 1
    assert result.actions[0].action == "get_health"
    assert result.actions[0].arguments == {"dataset_id": "ds-1"}


def test_unknown_function_call_is_rejected():
    response = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[
                        SimpleNamespace(
                            text=None,
                            functionCall=SimpleNamespace(
                                name="delete_everything",
                                args={},
                            ),
                        )
                    ]
                )
            )
        ]
    )

    registry = SimpleNamespace(
        names=lambda: ("get_health",),
        to_function_declarations=lambda: (),
    )
    model = FakeModel(response)

    agent = CopilotAgent(
        model=model,
        model_name="test-model",
        tool_registry=registry,
    )

    with pytest.raises(ValueError, match="Unknown Copilot tool"):
        agent.respond("do something unsafe")

def test_registered_tools_are_sent_to_model():
    response = SimpleNamespace(candidates=[])

    class FakeRegistry:
        def names(self):
            return ("get_health",)

        def to_function_declarations(self):
            from google.genai import types

            return (
                types.FunctionDeclaration(
                    name="get_health",
                    description="Read dataset health.",
                    parametersJsonSchema={
                        "type": "object",
                        "properties": {
                            "dataset_id": {"type": "string"},
                        },
                        "required": ["dataset_id"],
                    },
                ),
            )

    model = FakeModel(response)
    agent = CopilotAgent(
        model=model,
        model_name="test-model",
        tool_registry=FakeRegistry(),
    )

    result = agent.respond("check dataset health")

    assert result.message == ""
    assert result.actions == ()
    assert len(model.calls) == 1

    config = model.calls[0]["config"]
    assert len(config.tools) == 1
    assert len(config.tools[0].function_declarations) == 1
    assert config.tools[0].function_declarations[0].name == "get_health"


def test_stream_returns_text_chunks():
    chunks = [
        SimpleNamespace(
            candidates=[
                SimpleNamespace(
                    content=SimpleNamespace(
                        parts=[SimpleNamespace(text="Hello ", functionCall=None)]
                    )
                )
            ]
        ),
        SimpleNamespace(
            candidates=[
                SimpleNamespace(
                    content=SimpleNamespace(
                        parts=[SimpleNamespace(text="from Copilot.", functionCall=None)]
                    )
                )
            ]
        ),
    ]

    class StreamingFakeModel(FakeModel):
        def generate_content_stream(self, **kwargs):
            self.calls.append(kwargs)
            return iter(chunks)

    model = StreamingFakeModel(None)
    agent = CopilotAgent(
        model=model,
        model_name="test-model",
        tool_registry=None,
    )

    result = list(agent.stream("hello"))

    assert result == ["Hello ", "from Copilot."]
    assert model.calls[0]["model"] == "test-model"

def test_stream_includes_prior_history_before_current_user():
    from application.copilot.contracts import CopilotTextEvent

    chunks = [
        SimpleNamespace(candidates=[]),
    ]

    class StreamingFakeModel(FakeModel):
        def generate_content_stream(self, **kwargs):
            self.calls.append(kwargs)
            return iter(chunks)

    model = StreamingFakeModel(None)
    agent = CopilotAgent(
        model=model,
        model_name="test-model",
        tool_registry=None,
    )

    history = (
        CopilotTextEvent(
            role="user",
            content="previous question",
        ),
        CopilotTextEvent(
            role="assistant",
            content="previous answer",
        ),
    )

    result = list(
        agent.stream(
            "current question",
            history=history,
        )
    )

    assert result == []

    contents = model.calls[0]["contents"]
    assert len(contents) == 3

    assert contents[0].role == "user"
    assert contents[0].parts[0].text == "previous question"

    assert contents[1].role == "model"
    assert contents[1].parts[0].text == "previous answer"

    assert contents[2].role == "user"
    assert contents[2].parts[0].text == "current question"


def test_stream_returns_registered_function_call_as_action():
    chunks = [
        SimpleNamespace(
            candidates=[
                SimpleNamespace(
                    content=SimpleNamespace(
                        parts=[
                            SimpleNamespace(
                                text=None,
                                functionCall=SimpleNamespace(
                                    name="get_health",
                                    args={"dataset_id": "ds-1"},
                                ),
                            )
                        ]
                    )
                )
            ]
        )
    ]

    class StreamingFakeModel(FakeModel):
        def generate_content_stream(self, **kwargs):
            self.calls.append(kwargs)
            return iter(chunks)

    registry = SimpleNamespace(
        names=lambda: ("get_health",),
        to_function_declarations=lambda: (),
    )
    model = StreamingFakeModel(None)

    agent = CopilotAgent(
        model=model,
        model_name="test-model",
        tool_registry=registry,
    )

    result = list(agent.stream("check dataset health"))

    assert len(result) == 1
    assert isinstance(result[0], CopilotAction)
    assert result[0].action == "get_health"
    assert result[0].arguments == {"dataset_id": "ds-1"}

def test_stream_sends_registered_tools_to_model():
    chunks = [
        SimpleNamespace(candidates=[]),
    ]

    class StreamingFakeModel(FakeModel):
        def generate_content_stream(self, **kwargs):
            self.calls.append(kwargs)
            return iter(chunks)

    class FakeRegistry:
        def names(self):
            return ("get_health",)

        def to_function_declarations(self):
            from google.genai import types

            return (
                types.FunctionDeclaration(
                    name="get_health",
                    description="Read dataset health.",
                    parametersJsonSchema={
                        "type": "object",
                        "properties": {
                            "dataset_id": {"type": "string"},
                        },
                        "required": ["dataset_id"],
                    },
                ),
            )

    model = StreamingFakeModel(None)
    agent = CopilotAgent(
        model=model,
        model_name="test-model",
        tool_registry=FakeRegistry(),
    )

    result = list(agent.stream("check dataset health"))

    assert result == []
    assert len(model.calls) == 1

    config = model.calls[0]["config"]
    assert len(config.tools) == 1
    assert len(config.tools[0].function_declarations) == 1
    assert config.tools[0].function_declarations[0].name == "get_health"

def test_respond_with_tool_result_continues_model_conversation():
    first_response = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[
                        SimpleNamespace(
                            text=None,
                            functionCall=SimpleNamespace(
                                id="call-1",
                                name="get_health",
                                args={"dataset_id": "ds-1"},
                            ),
                        )
                    ]
                )
            )
        ]
    )

    final_response = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[
                        SimpleNamespace(
                            text="Dataset is healthy.",
                            functionCall=None,
                        )
                    ]
                )
            )
        ]
    )

    class ContinuationFakeModel(FakeModel):
        def __init__(self):
            super().__init__(first_response)
            self.responses = [first_response, final_response]

        def generate_content(self, **kwargs):
            self.calls.append(kwargs)
            return self.responses.pop(0)

    registry = SimpleNamespace(
        names=lambda: ("get_health",),
        to_function_declarations=lambda: (),
    )

    model = ContinuationFakeModel()

    agent = CopilotAgent(
        model=model,
        model_name="test-model",
        tool_registry=registry,
    )

    first = agent.respond("check dataset health")

    assert first.actions[0].call_id == "call-1"

    result = agent.respond_with_tool_result(
        user_message="check dataset health",
        action=first.actions[0],
        tool_result={"status": "healthy"},
    )

    assert result.message == "Dataset is healthy."
    assert result.actions == ()
    assert len(model.calls) == 2

    continuation_contents = model.calls[1]["contents"]

    assert isinstance(continuation_contents, list)
    assert continuation_contents[0].parts[0].text == "check dataset health"
    assert continuation_contents[1].parts[0].function_call.name == "get_health"
    assert continuation_contents[1].parts[0].function_call.id == "call-1"
    assert continuation_contents[2].parts[0].function_response.name == "get_health"
    assert continuation_contents[2].parts[0].function_response.id == "call-1"
    assert continuation_contents[2].parts[0].function_response.response == {
        "status": "healthy"
    }




def test_respond_with_tool_result_includes_prior_session_history():
    from application.copilot.contracts import (
        CopilotTextEvent,
        CopilotToolCallEvent,
        CopilotToolResultEvent,
    )

    first_response = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[
                        SimpleNamespace(
                            text="Dataset is healthy.",
                            functionCall=None,
                        )
                    ]
                )
            )
        ]
    )

    class HistoryFakeModel(FakeModel):
        def generate_content(self, **kwargs):
            self.calls.append(kwargs)
            return first_response

    registry = SimpleNamespace(
        names=lambda: ("get_health",),
        to_function_declarations=lambda: (),
    )

    model = HistoryFakeModel(first_response)

    agent = CopilotAgent(
        model=model,
        model_name="test-model",
        tool_registry=registry,
    )

    action = CopilotAction(
        action="get_health",
        arguments={"dataset_id": "ds-1"},
        call_id="call-1",
    )

    history = (
        CopilotTextEvent(
            role="user",
            content="check dataset health",
        ),
        CopilotToolCallEvent(action=action),
        CopilotToolResultEvent(
            action=action,
            result={"status": "healthy"},
        ),
        CopilotTextEvent(
            role="assistant",
            content="Dataset is healthy.",
        ),
    )

    result = agent.respond_with_tool_result(
        user_message="check something else",
        action=action,
        tool_result={"status": "healthy"},
        history=history,
    )

    assert result.message == "Dataset is healthy."
    assert len(model.calls) == 1

    contents = model.calls[0]["contents"]

    assert contents[0].role == "user"
    assert contents[0].parts[0].text == "check dataset health"

    assert contents[1].role == "model"
    assert contents[1].parts[0].function_call.name == "get_health"
    assert contents[1].parts[0].function_call.id == "call-1"

    assert contents[2].role == "user"
    assert contents[2].parts[0].function_response.name == "get_health"
    assert contents[2].parts[0].function_response.id == "call-1"

    assert contents[3].role == "model"
    assert contents[3].parts[0].text == "Dataset is healthy."

    assert contents[4].role == "user"
    assert contents[4].parts[0].text == "check something else"


def test_stream_preserves_function_call_id():
    function_call = SimpleNamespace(
        id="call-stream-1",
        name="get_health",
        args={"dataset_id": "ds-1"},
    )

    chunks = [
        SimpleNamespace(
            candidates=[
                SimpleNamespace(
                    content=SimpleNamespace(
                        parts=[
                            SimpleNamespace(
                                text=None,
                                functionCall=function_call,
                            )
                        ]
                    )
                )
            ]
        )
    ]

    class StreamingFakeModel(FakeModel):
        def generate_content_stream(self, **kwargs):
            self.calls.append(kwargs)
            return iter(chunks)

    model = StreamingFakeModel(None)

    registry = SimpleNamespace(
        names=lambda: ("get_health",),
        to_function_declarations=lambda: (),
    )

    agent = CopilotAgent(
        model=model,
        model_name="test-model",
        tool_registry=registry,
    )

    result = list(agent.stream("check dataset health"))

    assert len(result) == 1
    assert isinstance(result[0], CopilotAction)
    assert result[0].action == "get_health"
    assert result[0].arguments == {"dataset_id": "ds-1"}
    assert result[0].call_id == "call-stream-1"


