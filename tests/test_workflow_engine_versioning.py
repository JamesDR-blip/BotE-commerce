import pandas as pd

from configs.settings import Settings
from domain.plans import ExecutionPlan, PlanStep
from services.container import build_container
from domain.identity import CurrentUser
from services.workspace_project_service import WorkspaceProjectService

def test_workflow_engine_executes_active_version():
    container = build_container(
        Settings(
            database_url="sqlite://",
        )
    )

    authoring_service = container.workflow_authoring
    workspace_projects = container.workspace_projects
    current_user = CurrentUser(
        user_id="test-user"
    )

    workspace_projects.create_workspace(
        current_user=current_user,
        workspace_id="ws-engine-version",
        name="Engine Version Workspace",
    )

    workspace_projects.create_project(
        current_user=current_user,
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

    authoring_service.save_workflow(
        current_user=current_user,
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

    authoring_service.create_workflow_version(
        current_user=current_user,
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
    authoring_service.activate_workflow_version(
        current_user=current_user,
        workflow_id="wf-engine-version",
        version="2.0",
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