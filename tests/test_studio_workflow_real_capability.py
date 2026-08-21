from domain.plans import ExecutionPlan, PlanStep
from configs.settings import Settings
from services.container import build_container
import pandas as pd


def test_studio_workflow_executes_real_capability():
    container = build_container(
        Settings(
            database_url="sqlite://",
        )
    )

    studio = container.studio

    studio.create_workspace(
        workspace_id="ws-1",
        name="Demo",
    )

    studio.create_project(
        project_id="p-1",
        workspace_id="ws-1",
        name="Catalog",
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="data.normalize",
                capability_version="1.0",
                parameters={},
            ),
        ),
        version="1.0",
        metadata={},
    )

    workflow = studio.save_workflow(
        workflow_id="wf-1",
        project_id="p-1",
        name="Normalize Catalog",
        version="1.0",
        plan=plan,
    )

    assert workflow.id == "wf-1"

    runtime = container.workflow_engine.execute(
        workflow_id="wf-1",
        execution_id="exec-1",
        inputs={
            "frame": pd.DataFrame(
                {
                    "product_title": [
                        "Nike Air Max 90 Black",
                        "Adidas Ultraboost White",
                    ]
                }
            ),
        }
    )

    assert runtime.success is True

    assert runtime.workflow_id == "wf-1"
    assert runtime.workflow_version == "1.0"

    assert runtime.outputs is not None