from __future__ import annotations

import pytest

from domain.capabilities import (
    CapabilityContext,
    CapabilityResult,
    CapabilitySpec,
)
from domain.capability_registry import CapabilityRegistry
from domain.plans import ExecutionPlan, PlanStep
from execution.capabilities.capability_executor import CapabilityExecutor


class TypedEchoCapability:
    @property
    def spec(self) -> CapabilitySpec:
        return CapabilitySpec(
            id="test.typed_echo",
            version="1.0",
            description="Typed echo capability",
            input_keys=("value",),
            output_keys=("result",),
            input_types={
                "value": str,
            },
            output_types={
                "result": str,
            },
        )

    def execute(
        self,
        context: CapabilityContext,
    ) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "result": context.inputs["value"],
            }
        )


class InvalidOutputCapability:
    @property
    def spec(self) -> CapabilitySpec:
        return CapabilitySpec(
            id="test.invalid_output",
            version="1.0",
            description="Invalid output capability",
            input_keys=("value",),
            output_keys=("result",),
            input_types={
                "value": str,
            },
            output_types={
                "result": str,
            },
        )

    def execute(
        self,
        context: CapabilityContext,
    ) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "result": 123,
            }
        )


def make_plan(capability_id: str) -> ExecutionPlan:
    return ExecutionPlan(
        steps=[
            PlanStep(
                capability_id=capability_id,
                capability_version="1.0",
            )
        ]
    )


def test_executor_accepts_valid_input_and_output_types():
    registry = CapabilityRegistry()
    registry.register(TypedEchoCapability())

    executor = CapabilityExecutor(registry)

    result = executor.execute(
        plan=make_plan("test.typed_echo"),
        inputs={
            "value": "hello",
        },
        execution_id="exec-1",
    )

    assert result["result"] == "hello"


def test_executor_rejects_invalid_input_type():
    registry = CapabilityRegistry()
    registry.register(TypedEchoCapability())

    executor = CapabilityExecutor(registry)

    with pytest.raises(
        TypeError,
        match="Invalid input type",
    ):
        executor.execute(
            plan=make_plan("test.typed_echo"),
            inputs={
                "value": 123,
            },
            execution_id="exec-1",
        )


def test_executor_rejects_invalid_output_type():
    registry = CapabilityRegistry()
    registry.register(InvalidOutputCapability())

    executor = CapabilityExecutor(registry)

    with pytest.raises(
        TypeError,
        match="Invalid output type",
    ):
        executor.execute(
            plan=make_plan("test.invalid_output"),
            inputs={
                "value": "hello",
            },
            execution_id="exec-1",
        )
