from services.container import Container
from configs.settings import Settings

from agents.requirement import ValidationRequirement


def test_multi_capability_request_builds_plan():

    container = Container(Settings())

    requirement = ValidationRequirement(
        requested_capabilities=(
            "data.extract",
            "data.validate",
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
        "data.extract",
        "data.clean",
        "data.validate",
    ]