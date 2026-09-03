from domain.plans import ExecutionPlan
from services.container import build_container
from configs.settings import Settings
from domain.identity import CurrentUser
from services.workspace_project_service import WorkspaceProjectService


class FakeCapabilityExecution:
    def execute_plan(
        self,
        *,
        plan,
        inputs,
        execution_id,
    ):
        return type(
            "Result",
            (),
            {
                "outputs": {
                    "result": "ok",
                },
                "trace": type(
                    "Trace",
                    (),
                    {
                        "execution_id": execution_id,
                        "records": (),
                    },
                )(),
            },
        )()


def test_studio_workflow_executes_through_runtime():
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
        workspace_id="ws-1",
        name="Demo",
    )

    workspace_projects.create_project(
        current_user=current_user,
        project_id="p-1",
        workspace_id="ws-1",
        name="Catalog",
    )

    plan = ExecutionPlan(
        steps=(),
        version="1.0",
        metadata={},
    )

    workflow = authoring_service.save_workflow(
        workflow_id="wf-1",
        project_id="p-1",
        name="Validation",
        version="1.0",
        plan=plan,
    )

    assert workflow.id == "wf-1"

    engine = container.workflow_engine

    engine.capability_execution = (
        FakeCapabilityExecution()
    )

    runtime = engine.execute(
        workflow_id="wf-1",
        execution_id="exec-1",
        inputs={
            "file": "products.csv",
        },
    )

    assert runtime.success is True

    assert runtime.workflow_id == "wf-1"

    assert runtime.workflow_version == "1.0"

    assert runtime.outputs == {
        "result": "ok",
    }

    execution = container.workflow_executions.get(
        "exec-1"
    )

    assert execution is not None

    assert execution.workflow_id == "wf-1"

    assert execution.workflow_version == "1.0"

    assert execution.status == "COMPLETED"