from domain.plan_adapter import (
    VALIDATION_CAPABILITY_ID,
    validation_execution_plan,
)


def test_validation_workflow_maps_to_validation_capability():
    plan = validation_execution_plan()

    assert len(plan.steps) == 1

    step = plan.steps[0]

    assert step.capability_id == VALIDATION_CAPABILITY_ID
    assert step.capability_version == "1.0"
    assert step.parameters == {}


def test_validation_execution_plan_contains_migration_metadata():
    plan = validation_execution_plan()

    assert plan.metadata["source"] == "legacy-validation-workflow"