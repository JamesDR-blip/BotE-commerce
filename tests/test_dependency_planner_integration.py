from agents.planner import PlannerAgent
from agents.requirement import ValidationRequirement

from domain.capability_registry import CapabilityRegistry
from domain.capabilities import (
    CapabilitySpec,
)
from domain.intent_resolver import IntentResolver
from domain.dependency_resolver import DependencyResolver


class FakeCapability:

    def __init__(self, spec):
        self.spec = spec

    def execute(self, context):
        pass


def test_planner_resolves_dependencies_in_execution_order():

    registry = CapabilityRegistry()

    registry.register(
        FakeCapability(
            CapabilitySpec(
                id="data.clean",
                version="1.0",
                description="Clean data",
                input_keys=("frame",),
                output_keys=("frame",),
            )
        )
    )

    registry.register(
        FakeCapability(
            CapabilitySpec(
                id="data.validate",
                version="1.0",
                description="Validate data",
                input_keys=("frame",),
                output_keys=("issues",),
                required_capabilities=(
                    "data.clean",
                ),
                input_mappings=(
                    ("frame", "frame"),
                ),
                intents=(
                    "validate_product_quality",
                ),
            )
        )
    )


    planner = PlannerAgent(
        registry=registry,
        resolver=DependencyResolver(),
        intent_resolver=IntentResolver(
            {
                "validate_product_quality": (
                    "data.validate",
                )
            }
        ),
    )


    plan = planner.plan(
        ValidationRequirement(
            requested_intents=(
                "validate_product_quality",
            )
        )
    )


    assert [
        step.capability_id
        for step in plan.steps
    ] == [
        "data.clean",
        "data.validate",
    ]


def test_planner_preserves_explicit_dependency_input_mapping():

    registry = CapabilityRegistry()

    registry.register(
        FakeCapability(
            CapabilitySpec(
                id="data.clean",
                version="1.0",
                description="Clean data",
                input_keys=("frame",),
                output_keys=("cleaned_frame",),
            )
        )
    )

    registry.register(
        FakeCapability(
            CapabilitySpec(
                id="data.validate",
                version="1.0",
                description="Validate data",
                input_keys=("frame",),
                output_keys=("issues",),
                required_capabilities=(
                    "data.clean",
                ),
                input_mappings=(
                    ("frame", "cleaned_frame"),
                ),
                intents=(
                    "validate_product_quality",
                ),
            )
        )
    )

    planner = PlannerAgent(
        registry=registry,
        resolver=DependencyResolver(),
        intent_resolver=IntentResolver(
            {
                "validate_product_quality": (
                    "data.validate",
                )
            }
        ),
    )

    plan = planner.plan(
        ValidationRequirement(
            requested_intents=(
                "validate_product_quality",
            )
        )
    )

    validate_step = next(
        step
        for step in plan.steps
        if step.capability_id == "data.validate"
    )

    assert validate_step.input_mapping == {
        "frame": "cleaned_frame",
    }


from domain.capabilities import CapabilityContext, CapabilityResult


class RealCleanCapability:

    def __init__(self, spec):
        self.spec = spec

    def execute(self, context):
        return CapabilityResult(
            outputs={
                "cleaned_frame": (
                    f"{context.inputs['frame']}-cleaned"
                )
            }
        )


class RealValidateCapability:

    def __init__(self, spec):
        self.spec = spec

    def execute(self, context):
        return CapabilityResult(
            outputs={
                "issues": (
                    context.inputs["frame"]
                )
            }
        )


def test_planned_dependency_mapping_executes_end_to_end():

    registry = CapabilityRegistry()

    registry.register(
        RealCleanCapability(
            CapabilitySpec(
                id="data.clean",
                version="1.0",
                description="Clean data",
                input_keys=("frame",),
                output_keys=("cleaned_frame",),
            )
        )
    )

    registry.register(
        RealValidateCapability(
            CapabilitySpec(
                id="data.validate",
                version="1.0",
                description="Validate data",
                input_keys=("frame",),
                output_keys=("issues",),
                required_capabilities=(
                    "data.clean",
                ),
                input_mappings=(
                    ("frame", "cleaned_frame"),
                ),
                intents=(
                    "validate_product_quality",
                ),
            )
        )
    )

    planner = PlannerAgent(
        registry=registry,
        resolver=DependencyResolver(),
        intent_resolver=IntentResolver(
            {
                "validate_product_quality": (
                    "data.validate",
                )
            }
        ),
    )

    plan = planner.plan(
        ValidationRequirement(
            requested_intents=(
                "validate_product_quality",
            )
        )
    )

    from services.capability_executor import CapabilityExecutor

    executor = CapabilityExecutor(registry)

    result = executor.execute(
        plan,
        inputs={
            "frame": "original",
        },
        execution_id="dependency-mapping-integration",
    )

    assert result["cleaned_frame"] == "original-cleaned"
    assert result["issues"] == "original-cleaned"