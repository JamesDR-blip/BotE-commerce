import json

from agents.requirement import WorkflowRequirement
from domain.plans import ExecutionPlan, PlanStep
from execution.context.service import (
    ExecutionContextService,
)
from infrastructure.serialization.execution_plan import (
    ExecutionPlanSerializer,
)
from infrastructure.serialization.requirement import (
    RequirementSerializer,
)
from .conftest import FakeExecutions


def test_execution_context_service_reconstructs_context():
    requirement = WorkflowRequirement(
        requested_category="Fashion",
        requested_capabilities=("data.qa",),
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="data.qa",
                capability_version="1.0",
            ),
        ),
        version="1.0",
        metadata={"source": "planner"},
    )

    repository = FakeExecutions(
        {
            "requirement_json": json.dumps(
                RequirementSerializer.to_dict(
                    requirement
                )
            ),
            "plan_json": json.dumps(
                ExecutionPlanSerializer.to_dict(
                    plan
                )
            ),
            "planner_version": "planner-1",
        }
    )

    service = ExecutionContextService(repository)

    context = service.get("execution-1")

    assert context is not None
    assert context.requirement == requirement
    assert context.plan == plan
    assert context.planner_version == "planner-1"


def test_execution_context_service_returns_none_for_missing_execution():
    repository = FakeExecutions(None)

    service = ExecutionContextService(repository)

    assert service.get("missing") is None



