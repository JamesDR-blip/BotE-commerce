from agents.planner import PlannerAgent
from agents.requirement import ValidationRequirement
from domain.intent_resolver import IntentResolver
from domain.capabilities import CapabilitySpec


def test_planner_resolves_requested_intent():

    planner = PlannerAgent(
        catalog={
            "data.validate": CapabilitySpec(
                id="data.validate",
                version="1.0",
                description="Validate",
                input_keys=("frame",),
                output_keys=("issues",),
            )
        },
        intent_resolver=IntentResolver(
            {
                "validate_product_quality": (
                    "data.validate",
                )
            }
        ),
    )

    requirement = ValidationRequirement(
        requested_intents=(
            "validate_product_quality",
        )
    )

    plan = planner.plan(requirement)

    assert plan.steps[0].capability_id == "data.validate"