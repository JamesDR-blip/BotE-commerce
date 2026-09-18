from dataclasses import dataclass

import pytest

from application.copilot.tools import CopilotTool, CopilotToolRegistry


@dataclass(frozen=True)
class ExampleArguments:
    dataset_id: str


def test_registry_validates_typed_arguments():
    calls = []

    def handler(*, arguments):
        calls.append(arguments)
        return arguments

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

    result = registry.invoke(
        "get_dataset",
        {"dataset_id": "dataset-1"},
    )

    assert isinstance(result, ExampleArguments)
    assert result.dataset_id == "dataset-1"
    assert calls == [result]


def test_registry_rejects_malformed_typed_arguments():
    calls = []

    def handler(*, arguments):
        calls.append(arguments)
        return arguments

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

    with pytest.raises(ValueError, match="Invalid arguments"):
        registry.invoke(
            "get_dataset",
            {"unexpected": "value"},
        )

    assert calls == []


def test_registry_does_not_accept_non_object_arguments():
    registry = CopilotToolRegistry()

    with pytest.raises(TypeError, match="must be an object"):
        registry.invoke("anything", ["not", "an", "object"])
