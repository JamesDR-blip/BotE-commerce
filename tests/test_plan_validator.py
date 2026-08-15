from __future__ import annotations

import pytest


from domain.capability_registry import CapabilityRegistry
from domain.plans import ExecutionPlan, PlanStep
from services.plan_validator import PlanValidator

class TypedEchoCapability:
    @property
    def spec(self):
        from domain.capabilities import CapabilitySpec

        return CapabilitySpec(
            id="test.typed_echo",
            version="1.0",
            description="typed echo",
            input_keys=("value",),
            output_keys=("result",),
        )

    def execute(self, context):
        from domain.capabilities import CapabilityResult

        return CapabilityResult(
            outputs={
                "result": context.inputs["value"]
            }
        )

def test_plan_validator_accepts_matching_version():
    registry = CapabilityRegistry()

    registry.register(
        TypedEchoCapability()
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.typed_echo",
                capability_version="1.0",
            ),
        )
    )

    PlanValidator().validate(
        plan,
        registry,
    )

def test_plan_validator_rejects_version_mismatch():
    registry = CapabilityRegistry()

    registry.register(
        TypedEchoCapability()
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.typed_echo",
                capability_version="2.0",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="version mismatch",
    ):
        PlanValidator().validate(
            plan,
            registry,
        )