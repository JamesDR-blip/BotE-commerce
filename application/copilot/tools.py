from dataclasses import MISSING, dataclass, fields, is_dataclass
from types import UnionType
from typing import Any, Callable, Union, get_args, get_origin


@dataclass(frozen=True)
class CopilotTool:
    """A single explicitly registered Copilot operation."""

    name: str
    description: str
    handler: Callable[..., Any]
    arguments_type: type[Any] | None = None


class CopilotToolRegistry:
    """Allowlisted registry for typed Copilot application tools."""

    def __init__(self, tools: tuple[CopilotTool, ...] = ()) -> None:
        names = [tool.name for tool in tools]

        if len(names) != len(set(names)):
            raise ValueError("Duplicate Copilot tool name")

        self._tools = {tool.name: tool for tool in tools}

    def names(self) -> tuple[str, ...]:
        return tuple(self._tools)

    def get(self, name: str) -> CopilotTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ValueError(f"Unknown Copilot tool: {name}") from exc

    def invoke(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        current_user: Any | None = None,
    ) -> Any:
        if not isinstance(arguments, dict):
            raise TypeError("Copilot tool arguments must be an object")

        tool = self.get(name)
        typed_arguments = self._validate_arguments(tool, arguments)

        if current_user is not None:
            return tool.handler(
                current_user=current_user,
                arguments=typed_arguments,
            )

        return tool.handler(arguments=typed_arguments)

    def to_function_declarations(self) -> tuple[Any, ...]:
        """Build provider-neutral-safe Gemini function declarations."""
        from google.genai import types

        declarations = []

        for tool in self._tools.values():
            declarations.append(
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parametersJsonSchema=self._arguments_type_to_json_schema(
                        tool.arguments_type
                    ),
                )
            )

        return tuple(declarations)

    @staticmethod
    def _validate_arguments(
        tool: CopilotTool,
        arguments: dict[str, Any],
    ) -> Any:
        arguments_type = tool.arguments_type

        if arguments_type is None:
            return arguments

        try:
            return arguments_type(**arguments)
        except TypeError as exc:
            raise ValueError(
                f"Invalid arguments for Copilot tool: {tool.name}"
            ) from exc

    @staticmethod
    def _python_type_to_json_schema(annotation: Any) -> dict[str, Any]:
        origin = get_origin(annotation)

        if origin in (Union, UnionType):
            return {
                "anyOf": [
                    CopilotToolRegistry._python_type_to_json_schema(item)
                    for item in get_args(annotation)
                ]
            }

        if annotation is str:
            return {"type": "string"}

        if annotation is int:
            return {"type": "integer"}

        if annotation is float:
            return {"type": "number"}

        if annotation is bool:
            return {"type": "boolean"}

        if origin is dict:
            return {"type": "object"}

        if origin is list:
            return {"type": "array"}

        if annotation is Any:
            return {}

        if annotation is type(None):
            return {"type": "null"}

        raise TypeError(
            f"Unsupported Copilot argument type: {annotation}"
        )

    @classmethod
    def _arguments_type_to_json_schema(
        cls,
        arguments_type: type[Any] | None,
    ) -> dict[str, Any]:
        if arguments_type is None:
            return {
                "type": "object",
                "properties": {},
            }

        if not is_dataclass(arguments_type):
            raise TypeError(
                "Copilot arguments type must be a dataclass: "
                f"{arguments_type}"
            )

        properties: dict[str, Any] = {}
        required: list[str] = []

        for item in fields(arguments_type):
            properties[item.name] = cls._python_type_to_json_schema(
                item.type
            )

            if item.default is MISSING and item.default_factory is MISSING:
                required.append(item.name)

        schema: dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }

        if required:
            schema["required"] = required

        return schema

