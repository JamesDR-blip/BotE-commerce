from domain.plans import ExecutionPlan
from domain.studio.runtime import WorkflowExecution


def test_workflow_execution_create():

    plan = ExecutionPlan(
        steps=(),
        version="1.0",
        metadata={},
    )

    runtime = WorkflowExecution(
        execution_id="exec-1",
        workflow_id="wf-1",
        workflow_version="1",
        plan=plan,
        inputs={
            "file": "products.csv"
        },
    )

    assert runtime.execution_id == "exec-1"

    assert runtime.workflow_id == "wf-1"

    assert runtime.plan.version == "1.0"

    assert runtime.success is False