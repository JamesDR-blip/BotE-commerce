from domain.execution_plan import ExecutionPlan as CompatibilityExecutionPlan
from domain.execution_plan import PlanStep as CompatibilityPlanStep
from domain.plans import ExecutionPlan, PlanStep


def test_plan_step_contains_capability_contract():
    step = PlanStep(
        capability_id="data.validate",
    )

    assert step.capability_id == "data.validate"
    assert step.capability_version == "1.0"
    assert step.parameters == {}


def test_plan_step_supports_parameters():
    step = PlanStep(
        capability_id="data.extract",
        capability_version="2.0",
        parameters={
            "attributes": ["brand", "color", "size"],
        },
    )

    assert step.capability_id == "data.extract"
    assert step.capability_version == "2.0"
    assert step.parameters["attributes"] == [
        "brand",
        "color",
        "size",
    ]


def test_execution_plan_preserves_step_order():
    plan = ExecutionPlan(
        steps=(
            PlanStep("data.clean"),
            PlanStep("data.extract"),
            PlanStep("data.validate"),
        )
    )

    assert [step.capability_id for step in plan.steps] == [
        "data.clean",
        "data.extract",
        "data.validate",
    ]


def test_execution_plan_has_version_and_metadata():
    plan = ExecutionPlan(
        steps=(
            PlanStep("data.validate"),
        ),
        version="1.0",
        metadata={
            "source": "planner",
        },
    )

    assert plan.version == "1.0"
    assert plan.metadata == {
        "source": "planner",
    }


def test_plan_is_immutable():
    plan = ExecutionPlan(
        steps=(
            PlanStep("data.validate"),
        )
    )

    try:
        plan.version = "2.0"
    except AttributeError:
        pass
    else:
        raise AssertionError("ExecutionPlan should be immutable")


def test_execution_plan_compatibility_module_uses_canonical_models():
    assert CompatibilityPlanStep is PlanStep
    assert CompatibilityExecutionPlan is ExecutionPlan