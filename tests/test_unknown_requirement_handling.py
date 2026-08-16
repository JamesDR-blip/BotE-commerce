import pytest

from services.container import Container
from configs.settings import Settings

from agents.requirement import ValidationRequirement


def test_unknown_capability_is_rejected():

    container = Container(Settings())

    requirement = ValidationRequirement(
        requested_capabilities=(
            "finance.forecast",
        )
    )

    with pytest.raises(Exception):
        container.planner.plan(
            requirement
        )