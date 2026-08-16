from services.container import Container
from configs.settings import Settings

from agents.requirement import ValidationRequirement

def test_user_request_builds_execution_plan():

    container = Container(Settings())

    requirement = container.agents.requirements.interpret(
        user_request=(
            "Kiểm tra chất lượng dữ liệu sản phẩm"
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