from agents.planner import PlannerAgent
from agents.requirement import ValidationRequirement
from domain.capabilities import CapabilitySpec
from domain.dependency_resolver import DependencyResolver
from domain.plans import ExecutionPlan
from capabilities.cleaning import CLEANING_CAPABILITY_SPEC
from capabilities.validation import VALIDATION_CAPABILITY_SPEC

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


def make_catalog() -> dict[str, CapabilitySpec]:
    return {
        "data.clean": make_spec("data.clean"),
        "data.extract": make_spec(
            "data.extract",
            required_capabilities=("data.clean",),
        ),
        "data.validate": make_spec(
            "data.validate",
            required_capabilities=("data.extract",),
        ),
    }


def test_planner_builds_execution_plan_from_requested_capabilities():
    planner = PlannerAgent(
        catalog=make_catalog(),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.validate",),
    )

    plan = planner.plan(requirement)

    assert isinstance(plan, ExecutionPlan)
    assert [step.capability_id for step in plan.steps] == [
        "data.clean",
        "data.extract",
        "data.validate",
    ]


def test_planner_preserves_capability_versions():
    catalog = {
        "data.clean": CapabilitySpec(
            id="data.clean",
            version="2.0",
            description="Clean data",
            input_keys=("frame",),
            output_keys=("clean_frame",),
        ),
    }

    planner = PlannerAgent(
        catalog=catalog,
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.clean",),
    )

    plan = planner.plan(requirement)

    assert len(plan.steps) == 1
    assert plan.steps[0].capability_id == "data.clean"
    assert plan.steps[0].capability_version == "2.0"


def test_planner_does_not_add_unrequested_capabilities():
    planner = PlannerAgent(
        catalog=make_catalog(),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.clean",),
    )

    plan = planner.plan(requirement)

    assert [step.capability_id for step in plan.steps] == [
        "data.clean",
    ]


def test_planner_marks_plan_source():
    planner = PlannerAgent(
        catalog=make_catalog(),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.clean",),
    )

    plan = planner.plan(requirement)

    assert plan.metadata["source"] == "planner"


def test_planner_can_build_plan_for_cleaning_and_validation():
    catalog = {
        CLEANING_CAPABILITY_SPEC.id: CLEANING_CAPABILITY_SPEC,
        VALIDATION_CAPABILITY_SPEC.id: VALIDATION_CAPABILITY_SPEC,
    }

    planner = PlannerAgent(
        catalog=catalog,
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=(
            "data.validate",
        ),
    )

    plan = planner.plan(requirement)

    assert [step.capability_id for step in plan.steps] == [
        "data.clean",
        "data.validate",
    ]


def test_planner_resolves_validation_dependencies():
    cleaning_spec = CapabilitySpec(
        id="data.clean",
        version="1.0",
        description="Clean ecommerce data",
        input_keys=("frame",),
        output_keys=("frame",),
    )

    validation_spec = CapabilitySpec(
        id="data.validate",
        version="1.0",
        description="Validate ecommerce data",
        input_keys=("frame",),
        output_keys=("validation_result",),
        required_capabilities=("data.clean",),
    )

    planner = PlannerAgent(
        catalog={
            "data.clean": cleaning_spec,
            "data.validate": validation_spec,
        },
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.validate",),
    )

    plan = planner.plan(requirement)

    assert [step.capability_id for step in plan.steps] == [
        "data.clean",
        "data.validate",
    ]