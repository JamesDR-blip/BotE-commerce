from dataclasses import dataclass

from application.copilot.tools import CopilotTool, CopilotToolRegistry
from application.copilot.tool_definitions import (
    GetHealthArguments,
    SimulateWorkflowArguments,
)


def _handler(**kwargs):
    return kwargs


def test_registry_builds_gemini_declarations_from_allowlist():
    registry = CopilotToolRegistry(
        tools=(
            CopilotTool(
                name="get_health",
                description="Read dataset health.",
                handler=_handler,
                arguments_type=GetHealthArguments,
            ),
            CopilotTool(
                name="simulate_workflow",
                description="Simulate a workflow.",
                handler=_handler,
                arguments_type=SimulateWorkflowArguments,
            ),
        )
    )

    declarations = registry.to_function_declarations()

    assert [item.name for item in declarations] == [
        "get_health",
        "simulate_workflow",
    ]
    assert declarations[0].description == "Read dataset health."
    assert declarations[1].description == "Simulate a workflow."


def test_gemini_declaration_contains_only_safe_argument_schema():
    registry = CopilotToolRegistry(
        tools=(
            CopilotTool(
                name="get_health",
                description="Read dataset health.",
                handler=_handler,
                arguments_type=GetHealthArguments,
            ),
        )
    )

    declaration = registry.to_function_declarations()[0]

    assert declaration.parameters_json_schema == {
        "type": "object",
        "properties": {
            "dataset_id": {"type": "string"},
        },
        "required": ["dataset_id"],
    }
    assert not hasattr(declaration, "handler")


def test_gemini_schema_supports_optional_and_object_arguments():
    registry = CopilotToolRegistry(
        tools=(
            CopilotTool(
                name="simulate_workflow",
                description="Simulate a workflow.",
                handler=_handler,
                arguments_type=SimulateWorkflowArguments,
            ),
        )
    )

    declaration = registry.to_function_declarations()[0]

    schema = declaration.parameters_json_schema

    assert schema["properties"]["workflow_id"] == {"type": "string"}
    assert schema["properties"]["inputs"] == {"type": "object"}
    assert schema["properties"]["dataset_id"] == {
        "anyOf": [
            {"type": "string"},
            {"type": "null"},
        ]
    }
    assert schema["required"] == ["workflow_id", "inputs"]

