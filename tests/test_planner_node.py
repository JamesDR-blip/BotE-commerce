from agents.nodes.planner import PlannerNode
from agents.planner import PlannerAgent
from agents.requirement import ValidationRequirement
from domain.capabilities import CapabilitySpec
from domain.dependency_resolver import DependencyResolver


def make_spec(
    capability_id: str,
    required_capabilities: tuple[str, ...] = (),
) -> CapabilitySpec:
    return CapabilitySpec(
        id=capability_id,
        version="1.0",
        description=f"{capability_id} capability",
        input_keys=("frame",),
        output_keys=("result",),
        required_capabilities=required_capabilities,
    )


def test_planner_node_writes_execution_plan_to_state():
    catalog = {
        "data.clean": make_spec("data.clean"),
        "data.validate": make_spec(
            "data.validate",
            required_capabilities=("data.clean",),
        ),
    }

    planner = PlannerAgent(
        catalog=catalog,
        resolver=DependencyResolver(),
    )

    node = PlannerNode(planner)

    state = {
        "requirement": ValidationRequirement(
            requested_capabilities=("data.validate",),
        ),
    }

    result = node(state)

    plan = result["execution_plan"]

    assert [
        step.capability_id
        for step in plan.steps
    ] == [
        "data.clean",
        "data.validate",
    ]


def test_planner_node_does_not_execute_capabilities():
    catalog = {
        "data.clean": make_spec("data.clean"),
    }

    planner = PlannerAgent(
        catalog=catalog,
        resolver=DependencyResolver(),
    )

    node = PlannerNode(planner)

    state = {
        "requirement": ValidationRequirement(
            requested_capabilities=("data.clean",),
        ),
    }

    result = node(state)

    assert "execution_plan" in result
    assert result["execution_plan"].steps[0].capability_id == "data.clean"