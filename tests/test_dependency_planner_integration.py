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