from domain.plans import ExecutionPlan, PlanStep
from infrastructure.serialization.execution_plan import ExecutionPlanSerializer


def test_execution_plan_round_trip() -> None:
    original = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="data.clean",
                capability_version="1.0",
                parameters={"remove_duplicates": True},
                input_mapping={"frame": "frame"},
            ),
            PlanStep(
                capability_id="data.extract",
                capability_version="1.0",
                parameters={"attributes": ["brand", "model"]},
                input_mapping={"frame": "frame"},
            ),
        ),
        version="1.0",
        metadata={"source": "planner"},
    )

    serialized = ExecutionPlanSerializer.to_dict(original)
    restored = ExecutionPlanSerializer.from_dict(serialized)

    assert restored == original


def test_execution_plan_serializes_empty_plan() -> None:
    plan = ExecutionPlan(
        steps=(),
        version="1.0",
        metadata={},
    )

    data = ExecutionPlanSerializer.to_dict(plan)

    assert data == {
        "version": "1.0",
        "steps": [],
        "metadata": {},
    }


def test_execution_plan_deserializes_missing_optional_fields() -> None:
    plan = ExecutionPlanSerializer.from_dict(
        {
            "steps": [
                {
                    "capability_id": "data.clean",
                    "capability_version": "1.0",
                }
            ]
        }
    )

    assert len(plan.steps) == 1
    assert plan.steps[0].capability_id == "data.clean"
    assert plan.steps[0].parameters == {}
    assert plan.steps[0].input_mapping == {}
    assert plan.version == "1.0"
    assert plan.metadata == {}
