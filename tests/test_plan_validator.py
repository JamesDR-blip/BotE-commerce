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
        external_inputs={"external_frame"},
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
            external_inputs={"external_frame"},
        )


def test_plan_validator_rejects_unknown_parameter():
    registry = CapabilityRegistry()

    registry.register(
        TypedEchoCapability()
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.typed_echo",
                capability_version="1.0",
                parameters={
                    "unknown": "value",
                },
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)unknown parameter",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"external_frame"},
        )


def test_plan_validator_rejects_unknown_input_mapping():
    registry = CapabilityRegistry()

    registry.register(
        TypedEchoCapability()
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.typed_echo",
                capability_version="1.0",
                input_mapping={
                    "unknown": "value",
                },
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)unknown input mapping",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"external_frame"},
        )


class CleanCapability:
    @property
    def spec(self):
        from domain.capabilities import CapabilitySpec

        return CapabilitySpec(
            id="test.clean",
            version="1.0",
            description="clean",
            input_keys=("frame",),
            output_keys=("cleaned_frame",),
        )

    def execute(self, context):
        from domain.capabilities import CapabilityResult

        return CapabilityResult(
            outputs={
                "cleaned_frame": context.inputs["frame"]
            }
        )


class ExtractCapability:
    @property
    def spec(self):
        from domain.capabilities import CapabilitySpec

        return CapabilitySpec(
            id="test.extract",
            version="1.0",
            description="extract",
            input_keys=("cleaned_frame",),
            output_keys=("extracted",),
        )

    def execute(self, context):
        from domain.capabilities import CapabilityResult

        return CapabilityResult(
            outputs={
                "extracted": context.inputs["cleaned_frame"]
            }
        )


def test_plan_validator_accepts_mapping_from_previous_step_output():
    registry = CapabilityRegistry()

    registry.register(CleanCapability())
    registry.register(ExtractCapability())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.clean",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.extract",
                capability_version="1.0",
                input_mapping={
                    "cleaned_frame": "cleaned_frame",
                },
            ),
        )
    )

    PlanValidator().validate(
        plan,
        registry,
        external_inputs={"external_frame"},
    )


def test_plan_validator_rejects_mapping_from_unknown_source():
    registry = CapabilityRegistry()

    registry.register(ExtractCapability())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.extract",
                capability_version="1.0",
                input_mapping={
                    "cleaned_frame": "does_not_exist",
                },
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)unknown input mapping source",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"external_frame"},
        )


def test_plan_validator_rejects_mapping_from_later_step():
    registry = CapabilityRegistry()

    registry.register(CleanCapability())
    registry.register(ExtractCapability())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.extract",
                capability_version="1.0",
                input_mapping={
                    "cleaned_frame": "cleaned_frame",
                },
            ),
            PlanStep(
                capability_id="test.clean",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)unknown input mapping source",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"external_frame"},
        )


def test_plan_validator_accepts_external_input_mapping():
    registry = CapabilityRegistry()

    registry.register(ExtractCapability())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.extract",
                capability_version="1.0",
                input_mapping={
                    "cleaned_frame": "external_frame",
                },
            ),
        )
    )

    PlanValidator().validate(
        plan,
        registry,
        external_inputs={"external_frame"},
    )