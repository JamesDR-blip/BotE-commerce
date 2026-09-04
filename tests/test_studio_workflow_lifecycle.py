from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base

from repositories.workspaces import WorkspaceRepository
from repositories.projects import ProjectRepository
from repositories.workflows import WorkflowRepository

from services.workflow_authoring_service import WorkflowAuthoringService
from services.workspace_project_service import WorkspaceProjectService

from domain.plans import ExecutionPlan
from domain.identity import CurrentUser


def build_services():
    engine = create_engine("sqlite://")

    Base.metadata.create_all(engine)

    sessions = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    workspaces = WorkspaceRepository(sessions)
    projects = ProjectRepository(sessions)
    workflows = WorkflowRepository(sessions)

    workspace_projects = WorkspaceProjectService(
        workspaces=workspaces,
        projects=projects,
    )

    authoring_service = WorkflowAuthoringService(
        workflows=workflows,
        projects=projects,
    )

    return workspace_projects, authoring_service

def test_studio_workflow_lifecycle():
    workspace_projects, authoring_service = build_services()
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

    plan_v1 = ExecutionPlan(
        steps=(),
        version="1.0",
        metadata={},
    )

    workflow = authoring_service.save_workflow(
        current_user=current_user,
        workflow_id="wf-1",
        project_id="p-1",
        name="Validation",
        version="1.0",
        plan=plan_v1,
    )

    assert workflow.id == "wf-1"

    loaded = authoring_service.get_workflow(
        current_user=CurrentUser(user_id="test-user"),
        workflow_id="wf-1",
    )

    assert loaded is not None
    assert loaded.name == "Validation"
    assert loaded.active_version == "1.0"

    workflows = authoring_service.list_workflows(
        current_user=current_user,
        project_id="p-1",
    )

    assert len(workflows) == 1
    assert workflows[0].id == "wf-1"

    plan_v2 = ExecutionPlan(
        steps=(),
        version="2.0",
        metadata={
            "description": "Improved validation"
        },
    )

    version = authoring_service.create_workflow_version(
        current_user=current_user,
        workflow_id="wf-1",
        version="2.0",
        plan=plan_v2,
    )

    assert version.version == "2.0"

    versions = authoring_service.list_workflow_versions(
        current_user=current_user,
        workflow_id="wf-1",
    )

    assert len(versions) == 2

    loaded_v2 = authoring_service.get_workflow_version(
        current_user=current_user,
        workflow_id="wf-1",
        version="2.0",
    )

    assert loaded_v2 is not None
    assert loaded_v2.version == "2.0"

    activated = authoring_service.activate_workflow_version(
        current_user=current_user,
        workflow_id="wf-1",
        version="2.0",
    )

    assert activated.active_version == "2.0"

    active = authoring_service.workflows.get_active_version(
        "wf-1"
    )

    assert active is not None
    assert active.version == "2.0"