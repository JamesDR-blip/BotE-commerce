from configs.settings import Settings
from services.container import build_container
from domain.identity import CurrentUser
from services.workspace_project_service import WorkspaceProjectService


def test_workflow_version_lifecycle():
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
        workspace_id="ws-version",
        name="Version Workspace",
    )

    workspace_projects.create_project(
        current_user=current_user,
        project_id="project-version",
        workspace_id="ws-version",
        name="Version Project",
    )

    from domain.plans import ExecutionPlan

    v1_plan = ExecutionPlan(
        steps=(),
        version="1.0",
        metadata={
            "name": "initial",
        },
    )

    workflow = authoring_service.save_workflow(
        workflow_id="wf-version",
        project_id="project-version",
        name="Versioned Workflow",
        version="1.0",
        plan=v1_plan,
    )

    assert workflow.active_version == "1.0"

    v2_plan = ExecutionPlan(
        steps=(),
        version="2.0",
        metadata={
            "name": "new",
        },
    )

    version = authoring_service.create_workflow_version(
        workflow_id="wf-version",
        version="2.0",
        plan=v2_plan,
    )

    assert version.version == "2.0"

    # Creating a new version must NOT automatically
    # change the active version.
    workflow = authoring_service.get_workflow(
        "wf-version"
    )

    assert workflow.active_version == "1.0"

    versions = authoring_service.list_workflow_versions(
        "wf-version"
    )

    assert [v.version for v in versions] == [
        "1.0",
        "2.0",
    ]

    authoring_service.activate_workflow_version(
        "wf-version",
        "2.0",
    )

    workflow = authoring_service.get_workflow(
        "wf-version"
    )

    assert workflow.active_version == "2.0"

    active = container.workflows.get_active_version(
        "wf-version"
    )

    assert active is not None
    assert active.version == "2.0"