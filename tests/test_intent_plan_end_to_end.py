from services.container import Container
from configs.settings import Settings

from agents.requirement import ValidationRequirement


def test_business_intent_builds_execution_plan():

    container = Container(Settings())

    requirement = ValidationRequirement(
        requested_intents=(
            "assess_data_quality",
        )
    )

    plan = container.planner.plan(
        requirement
    )

    capability_ids = [
        step.capability_id
        for step in plan.steps
    ]

    assert capability_ids == [
        "data.clean",
        "data.validate",
        "data.qa",
    ]