import pytest

from agents.planner import PlannerAgent
from agents.router import WorkflowRouter


def test_router_selects_validation_workflow() -> None:
    router = WorkflowRouter()

    state = {
        "plan": (
            "requirements",
            "classify",
            "retrieve_rules",
            "extract",
            "autofix",
            "validate",
            "qa",
        )
    }

    assert router.route(state) == "validation"


def test_router_rejects_unsupported_plan() -> None:
    router = WorkflowRouter()

    state = {
        "plan": (
            "requirements",
            "classify",
        )
    }

    with pytest.raises(ValueError, match="Unsupported workflow plan"):
        router.route(state)


def test_planner_output_is_accepted_by_router() -> None:
    planner = PlannerAgent()
    router = WorkflowRouter()

    state = {
        "categories": ["Fashion"],
    }

    planned_state = planner.plan(state)

    assert router.route(planned_state) == "validation"


def test_planner_rejects_empty_categories() -> None:
    planner = PlannerAgent()

    with pytest.raises(
        ValueError,
        match="No validator categories are registered",
    ):
        planner.plan({"categories": []})


def test_router_rejects_unknown_workflow_step() -> None:
    router = WorkflowRouter()

    state = {
        "plan": (
            "requirements",
            "classify",
            "unknown_step",
            "qa",
        )
    }

    with pytest.raises(
        ValueError,
        match="Unsupported workflow plan",
    ):
        router.route(state)