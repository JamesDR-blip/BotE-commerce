from configs.settings import Settings
from services.container import Container
from agents.requirement import ValidationRequirement


def test_real_business_intent_builds_quality_pipeline():

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