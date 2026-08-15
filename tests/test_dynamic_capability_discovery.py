from agents.planner import PlannerAgent
from agents.requirement import ValidationRequirement
from domain.capabilities import (
    CapabilityContext,
    CapabilityResult,
    CapabilitySpec,
)
from domain.capability_registry import CapabilityRegistry
from domain.intent_resolver import IntentResolver


class MappingCapability:

    spec = CapabilitySpec(
        id="data.mapping",
        version="1.0",
        description="Map marketplace product data.",
        input_keys=(
            "frame",
        ),
        output_keys=(
            "mapped_frame",
        ),
        intents=(
            "map_marketplace_product",
        ),
    )

    def execute(
        self,
        context: CapabilityContext,
    ) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "mapped_frame": context.inputs["frame"]
            }
        )


def test_new_capability_is_discovered_without_planner_change():

    registry = CapabilityRegistry()

    registry.register(
        MappingCapability()
    )

    planner = PlannerAgent(
        registry=registry,
        intent_resolver=IntentResolver(
            {
                "map_marketplace_product": (
                    "data.mapping",
                )
            }
        ),
    )

    requirement = ValidationRequirement(
        requested_intents=(
            "map_marketplace_product",
        )
    )

    plan = planner.plan(
        requirement
    )

    assert [
        step.capability_id
        for step in plan.steps
    ] == [
        "data.mapping",
    ]