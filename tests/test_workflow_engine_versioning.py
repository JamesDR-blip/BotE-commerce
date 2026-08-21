import pandas as pd

from configs.settings import Settings
from domain.plans import ExecutionPlan, PlanStep
from services.container import build_container


def test_workflow_engine_executes_active_version():
    container = build_container(
        Settings(
            database_url="sqlite://",
        )
    )

    studio = container.studio

    studio.create_workspace(
        workspace_id="ws-engine-version",
        name="Engine Version Workspace",
    )

    studio.create_project(
        project_id="project-engine-version",
        workspace_id="ws-engine-version",
        name="Engine Version Project",
    )

    v1_plan = ExecutionPlan(
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

    studio.save_workflow(
        workflow_id="wf-engine-version",
        project_id="project-engine-version",
        name="Versioned Normalize",
        version="1.0",
        plan=v1_plan,
    )

    v2_plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="data.normalize",
                capability_version="1.0",
                parameters={},
            ),
        ),
        version="2.0",
        metadata={
            "version_marker": "v2",
        },
    )

    studio.create_workflow_version(
        workflow_id="wf-engine-version",
        version="2.0",
        plan=v2_plan,
    )

    # v1 remains active.
    runtime_v1 = container.workflow_engine.execute(
        workflow_id="wf-engine-version",
        execution_id="exec-v1",
        inputs={
            "frame": pd.DataFrame(
                {
                    "product_title": [
                        "Nike Air Max 90",
                    ],
                }
            ),
        },
    )

    assert runtime_v1.success is True
    assert runtime_v1.workflow_version == "1.0"

    # Activate v2.
    studio.activate_workflow_version(
        "wf-engine-version",
        "2.0",
    )

    runtime_v2 = container.workflow_engine.execute(
        workflow_id="wf-engine-version",
        execution_id="exec-v2",
        inputs={
            "frame": pd.DataFrame(
                {
                    "product_title": [
                        "Nike Air Max 90",
                    ],
                }
            ),
        },
    )

    assert runtime_v2.success is True
    assert runtime_v2.workflow_version == "2.0"