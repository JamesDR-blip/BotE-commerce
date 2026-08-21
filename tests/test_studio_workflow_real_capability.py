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


def test_studio_workflow_executes_real_capability_chain():
    container = build_container(
        Settings(
            database_url="sqlite://",
        )
    )

    studio = container.studio

    studio.create_workspace(
        workspace_id="ws-chain",
        name="Demo Chain",
    )

    studio.create_project(
        project_id="p-chain",
        workspace_id="ws-chain",
        name="Catalog Chain",
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="data.clean",
                capability_version="1.0",
                parameters={},
            ),
            PlanStep(
                capability_id="data.validate",
                capability_version="1.0",
                parameters={},
                input_mapping={
                    "frame": "frame",
                    "category": "category",
                },
            ),
        ),
        version="1.0",
        metadata={},
    )

    workflow = studio.save_workflow(
        workflow_id="wf-chain",
        project_id="p-chain",
        name="Clean and Validate Catalog",
        version="1.0",
        plan=plan,
    )

    assert workflow.id == "wf-chain"

    runtime = container.workflow_engine.execute(
        workflow_id="wf-chain",
        execution_id="exec-chain",
        inputs={
            "frame": pd.DataFrame(
                {
                    "product_title": [
                        "Nike Air Max 90",
                        "Adidas Ultraboost",
                    ],
                }
            ),
        },
    )

    assert runtime.success is True

    assert runtime.workflow_id == "wf-chain"
    assert runtime.workflow_version == "1.0"

    assert "frame" in runtime.outputs
    assert "category" in runtime.outputs
    assert "issues" in runtime.outputs
    assert "rule_version" in runtime.outputs

    assert isinstance(
        runtime.outputs["frame"],
        pd.DataFrame,
    )

    assert isinstance(
        runtime.outputs["category"],
        str,
    )

    assert isinstance(
        runtime.outputs["issues"],
        list,
    )

    assert isinstance(
        runtime.outputs["rule_version"],
        str,
    )