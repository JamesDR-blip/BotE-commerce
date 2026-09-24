from __future__ import annotations

from typing import Any

from application.copilot.contracts import CopilotAction, CopilotResponse
from application.copilot.tools import CopilotToolRegistry
from infrastructure.observability.telemetry import tracer


class CopilotAgent:
    """Provider-facing Copilot boundary with a fixed application tool allowlist."""

    def __init__(
        self,
        *,
        model: Any,
        model_name: str,
        tool_registry: CopilotToolRegistry | Any | None,
    ) -> None:
        self._model = model
        self._model_name = model_name
        self._tool_registry = tool_registry

    def stream(
        self,
        user_message: str,
        *,
        history: tuple[Any, ...] | None = None,
    ):
        """Stream text deltas from the configured provider."""
        config = self._build_config()

        contents: Any = user_message

        if history:
            from google.genai import types

            contents = self._history_to_contents(history)
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part(text=user_message),
                    ],
                )
            )

        with tracer(__name__).start_as_current_span(
            "agent.reasoning"
        ) as span:
            span.set_attribute("agent.type", "copilot")
            span.set_attribute("agent.operation", "stream")
            span.set_attribute("model.name", self._model_name)

            response_stream = self._model.generate_content_stream(
                model=self._model_name,
                contents=contents,
                config=config,
            )

            for response in response_stream:
                for candidate in response.candidates or []:
                    content = candidate.content
                    if content is None:
                        continue

                    for part in content.parts or []:
                        function_call = getattr(part, "functionCall", None)

                        if function_call is not None:
                            name = function_call.name
                            self._validate_tool(name)

                            yield CopilotAction(
                                action=name,
                                arguments=dict(function_call.args or {}),
                                call_id=getattr(function_call, "id", None),
                            )
                            continue

                        text = getattr(part, "text", None)
                        if text:
                            yield text

    def respond(self, user_message: str) -> CopilotResponse:
        with tracer(__name__).start_as_current_span(
            "agent.reasoning"
        ) as span:
            span.set_attribute("agent.type", "copilot")
            span.set_attribute("agent.operation", "respond")
            span.set_attribute("model.name", self._model_name)

            response = self._model.generate_content(
                model=self._model_name,
                contents=user_message,
                config=self._build_config(),
            )

            return self._parse_response(response)

    def respond_with_tool_result(
        self,
        *,
        user_message: str,
        action: CopilotAction,
        tool_result: Any,
        history: tuple[Any, ...] | None = None,
    ) -> CopilotResponse:
        """Continue a model turn after one registered tool has been executed."""
        self._validate_tool(action.action)

        from google.genai import types

        function_call = types.FunctionCall(
            id=action.call_id,
            name=action.action,
            args=dict(action.arguments),
        )

        function_response = types.FunctionResponse(
            id=action.call_id,
            name=action.action,
            response=(
                tool_result
                if isinstance(tool_result, dict)
                else {"result": tool_result}
            ),
        )

        contents = self._history_to_contents(history or ())

        contents.extend(
            [
                types.Content(
                    role="user",
                    parts=[
                        types.Part(text=user_message),
                    ],
                ),
                types.Content(
                    role="model",
                    parts=[
                        types.Part(functionCall=function_call),
                    ],
                ),
                types.Content(
                    role="user",
                    parts=[
                        types.Part(functionResponse=function_response),
                    ],
                ),
            ]
        )

        with tracer(__name__).start_as_current_span(
            "agent.reasoning"
        ) as span:
            span.set_attribute("agent.type", "copilot")
            span.set_attribute("agent.operation", "tool_result")
            span.set_attribute("model.name", self._model_name)

            response = self._model.generate_content(
                model=self._model_name,
                contents=contents,
                config=self._build_config(),
            )

            return self._parse_response(response)

    def _history_to_contents(
        self,
        history: tuple[Any, ...],
    ) -> list[Any]:
        from google.genai import types

        from application.copilot.contracts import (
            CopilotTextEvent,
            CopilotToolCallEvent,
            CopilotToolResultEvent,
        )

        contents: list[Any] = []

        for event in history:
            if isinstance(event, CopilotTextEvent):
                role = "model" if event.role == "assistant" else event.role
                contents.append(
                    types.Content(
                        role=role,
                        parts=[
                            types.Part(text=event.content),
                        ],
                    )
                )
                continue

            if isinstance(event, CopilotToolCallEvent):
                self._validate_tool(event.action.action)
                contents.append(
                    types.Content(
                        role="model",
                        parts=[
                            types.Part(
                                functionCall=types.FunctionCall(
                                    id=event.action.call_id,
                                    name=event.action.action,
                                    args=dict(event.action.arguments),
                                )
                            )
                        ],
                    )
                )
                continue

            if isinstance(event, CopilotToolResultEvent):
                self._validate_tool(event.action.action)
                result = (
                    event.result
                    if isinstance(event.result, dict)
                    else {"result": event.result}
                )
                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part(
                                functionResponse=types.FunctionResponse(
                                    id=event.action.call_id,
                                    name=event.action.action,
                                    response=result,
                                )
                            )
                        ],
                    )
                )
                continue

            raise TypeError(
                f"Unsupported Copilot history event: {type(event).__name__}"
            )

        return contents

    def _build_config(self) -> Any:
        if self._tool_registry is None:
            return None

        from google.genai import types

        declarations = self._tool_registry.to_function_declarations()

        return types.GenerateContentConfig(
            tools=[
                types.Tool(
                    function_declarations=list(declarations),
                )
            ]
        )

    def _validate_tool(self, name: str) -> None:
        if self._tool_registry is None or name not in self._tool_registry.names():
            raise ValueError(f"Unknown Copilot tool: {name}")

    def _parse_response(self, response: Any) -> CopilotResponse:
        message_parts: list[str] = []
        actions: list[CopilotAction] = []

        for candidate in response.candidates or []:
            content = candidate.content
            if content is None:
                continue

            for part in content.parts or []:
                function_call = getattr(part, "functionCall", None)

                if function_call is not None:
                    name = function_call.name
                    self._validate_tool(name)

                    actions.append(
                        CopilotAction(
                            action=name,
                            arguments=dict(function_call.args or {}),
                            call_id=getattr(function_call, "id", None),
                        )
                    )
                    continue

                text = getattr(part, "text", None)
                if text:
                    message_parts.append(text)

        return CopilotResponse(
            message="".join(message_parts),
            actions=tuple(actions),
        )
