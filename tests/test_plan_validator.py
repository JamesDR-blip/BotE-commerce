from __future__ import annotations

import pytest
import pandas as pd


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
        external_inputs={"value"},
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
        external_inputs={"frame"},
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


def test_plan_validator_rejects_required_input_without_mapping_or_external_input():
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

    with pytest.raises(
        ValueError,
        match=r"(?i)missing required input",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs=set(),
        )


def test_plan_validator_accepts_unmapped_input_when_external_input_exists():
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
        external_inputs={"value"},
    )


def test_plan_validator_accepts_mapped_input_from_previous_output():
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
        external_inputs={"frame"},
    )


def test_plan_validator_rejects_mapping_from_current_step_output():
    registry = CapabilityRegistry()

    registry.register(
        CleanCapability()
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.clean",
                capability_version="1.0",
                input_mapping={
                    "frame": "cleaned_frame",
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
            external_inputs={"frame"},
        )


def test_plan_validator_rejects_output_collision():
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
            PlanStep(
                capability_id="test.typed_echo",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)output collision",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"value"},
        )


class TypedProducerCapability:
    @property
    def spec(self):
        from domain.capabilities import CapabilitySpec

        return CapabilitySpec(
            id="test.typed_producer",
            version="1.0",
            description="typed producer",
            input_keys=("value",),
            output_keys=("cleaned_frame",),
            output_types={
                "cleaned_frame": str,
            },
        )

    def execute(self, context):
        from domain.capabilities import CapabilityResult

        return CapabilityResult(
            outputs={
                "cleaned_frame": "invalid-frame",
            }
        )


class TypedConsumerCapability:
    @property
    def spec(self):
        from domain.capabilities import CapabilitySpec

        return CapabilitySpec(
            id="test.typed_consumer",
            version="1.0",
            description="typed consumer",
            input_keys=("frame",),
            output_keys=("result",),
            input_types={
                "frame": pd.DataFrame,
            },
        )

    def execute(self, context):
        from domain.capabilities import CapabilityResult

        return CapabilityResult(
            outputs={
                "result": context.inputs["frame"],
            }
        )

def test_plan_validator_rejects_incompatible_mapping_types():
    registry = CapabilityRegistry()

    registry.register(
        TypedProducerCapability()
    )

    registry.register(
        TypedConsumerCapability()
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.typed_producer",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.typed_consumer",
                capability_version="1.0",
                input_mapping={
                    "frame": "cleaned_frame",
                },
            ),
        )
    )

    with pytest.raises(
        TypeError,
        match=r"(?i)incompatible input type",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"value"},
        )


def test_plan_validator_rejects_output_type_collision():
    registry = CapabilityRegistry()

    class StringOutputCapability:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.string_output",
                version="1.0",
                description="string output",
                input_keys=("value",),
                output_keys=("value",),
                output_types={
                    "value": str,
                },
            )

    class IntOutputCapability:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.int_output",
                version="1.0",
                description="int output",
                input_keys=("value",),
                output_keys=("value",),
                output_types={
                    "value": int,
                },
            )

    registry.register(StringOutputCapability())
    registry.register(IntOutputCapability())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.string_output",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.int_output",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)output collision",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"value"},
        )