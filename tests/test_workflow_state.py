from domain.plans import ExecutionPlan, PlanStep
from agents.state import WorkflowState


def test_workflow_state_supports_capability_execution_plan():
    execution_plan = ExecutionPlan(
        steps=(
            PlanStep("data.validate"),
        )
    )

    state: WorkflowState = {
        "execution_plan": execution_plan,
    }

    assert state["execution_plan"] is execution_plan
    assert state["execution_plan"].steps[0].capability_id == "data.validate"


def test_workflow_state_keeps_legacy_plan():
    state: WorkflowState = {
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

    assert state["plan"][-1] == "qa"


def test_workflow_state_supports_both_plan_contracts():
    execution_plan = ExecutionPlan(
        steps=(
            PlanStep("data.validate"),
        )
    )

    state: WorkflowState = {
        "plan": (
            "requirements",
            "classify",
            "retrieve_rules",
            "extract",
            "autofix",
            "validate",
            "qa",
        ),
        "execution_plan": execution_plan,
    }

    assert state["plan"]
    assert state["execution_plan"].steps[0].capability_id == "data.validate"