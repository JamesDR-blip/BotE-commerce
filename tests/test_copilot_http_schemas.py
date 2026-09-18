from application.copilot.contracts import CopilotAction, CopilotResponse
from domain.plans import ExecutionPlan, PlanStep
from domain.requirement import WorkflowRequirement
from schemas.copilot import (
    CopilotAuthorWorkflowResponse,
    CopilotPlanStepResponse,
    CopilotWorkflowPlanResponse,
)


def test_copilot_http_plan_schema_is_json_safe():
    response = CopilotAuthorWorkflowResponse(
        message="Workflow plan authored successfully.",
        project_id="project-1",
        name="Product cleanup",
        requested_category=None,
        requested_capabilities=["data.cleaning"],
        requested_intents=["clean"],
        parameters={"data.cleaning": {"mode": "safe"}},
        plan=CopilotWorkflowPlanResponse(
            version="1.0",
            steps=[
                CopilotPlanStepResponse(
                    capability_id="data.cleaning",
                    capability_version="1.0",
                    parameters={"mode": "safe"},
                    input_mapping={},
                )
            ],
            metadata={"source": "copilot"},
        ),
    )

    payload = response.model_dump(mode="json")

    assert payload["project_id"] == "project-1"
    assert payload["plan"]["steps"][0]["capability_id"] == "data.cleaning"
    assert payload["plan"]["steps"][0]["parameters"] == {"mode": "safe"}


def test_domain_copilot_response_is_not_the_http_contract():
    requirement = WorkflowRequirement(
        requested_capabilities=("data.cleaning",),
        requested_intents=("clean",),
    )
    plan = ExecutionPlan(
        steps=(PlanStep(capability_id="data.cleaning"),),
    )

    response = CopilotResponse(
        message="Workflow plan authored successfully.",
        actions=(
            CopilotAction(
                action="workflow_plan",
                arguments={
                    "requirement": requirement,
                    "plan": plan,
                },
            ),
        ),
    )

    assert response.actions[0].arguments["requirement"] is requirement
    assert response.actions[0].arguments["plan"] is plan
