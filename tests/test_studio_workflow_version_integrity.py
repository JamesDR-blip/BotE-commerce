import pytest

from database.models import Base

from domain.plans import ExecutionPlan
from domain.identity import CurrentUser

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from repositories.workspaces import WorkspaceRepository
from repositories.projects import ProjectRepository
from repositories.workflows import WorkflowRepository

from services.workflow_authoring_service import WorkflowAuthoringService
from services.workspace_project_service import WorkspaceProjectService

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


def test_workflow_versions_are_immutable_snapshots():
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
        metadata={
            "stage": "initial",
        },
    )

    authoring_service.save_workflow(
        current_user=current_user,
        workflow_id="wf-1",
        project_id="p-1",
        name="Validation",
        version="1.0",
        plan=plan_v1,
    )

    v1_before = authoring_service.get_workflow_version(
        current_user=current_user,
        workflow_id="wf-1",
        version="1.0",
    )

    assert v1_before is not None

    original_v1_plan = v1_before.plan_json

    plan_v2 = ExecutionPlan(
        steps=(),
        version="2.0",
        metadata={
            "stage": "improved",
        },
    )

    authoring_service.create_workflow_version(
        current_user=current_user,
        workflow_id="wf-1",
        version="2.0",
        plan=plan_v2,
    )

    authoring_service.activate_workflow_version(
        current_user=current_user,
        workflow_id="wf-1",
        version="2.0",
    )

    v1_after = authoring_service.get_workflow_version(
        current_user=current_user,
        workflow_id="wf-1",
        version="1.0",
    )

    v2 = authoring_service.get_workflow_version(
        current_user=current_user,
        workflow_id="wf-1",
        version="2.0",
    )

    assert v1_after is not None
    assert v2 is not None

    assert v1_after.plan_json == original_v1_plan
    assert v2.plan_json != v1_after.plan_json

    workflow = authoring_service.get_workflow(
        current_user=CurrentUser(user_id="test-user"),
        workflow_id="wf-1",
    )

    assert workflow is not None
    assert workflow.active_version == "2.0"

def test_other_user_cannot_create_workflow_version():
    workspace_projects, authoring_service = build_services()

    owner = CurrentUser(user_id="owner")
    other_user = CurrentUser(user_id="other-user")

    workspace_projects.create_workspace(
        current_user=owner,
        workspace_id="ws-owner",
        name="Owner Workspace",
    )

    workspace_projects.create_project(
        current_user=owner,
        project_id="project-owner",
        workspace_id="ws-owner",
        name="Owner Project",
    )

    plan_v1 = ExecutionPlan(
        steps=(),
        version="1.0",
        metadata={},
    )

    authoring_service.save_workflow(
        current_user=owner,
        workflow_id="wf-owner",
        project_id="project-owner",
        name="Owner Workflow",
        version="1.0",
        plan=plan_v1,
    )

    plan_v2 = ExecutionPlan(
        steps=(),
        version="2.0",
        metadata={},
    )

    with pytest.raises(
        ValueError,
        match="Workflow not found",
    ):
        authoring_service.create_workflow_version(
            current_user=other_user,
            workflow_id="wf-owner",
            version="2.0",
            plan=plan_v2,
        )

def test_other_user_cannot_list_workflow_versions():
    workspace_projects, authoring_service = build_services()

    owner = CurrentUser(user_id="owner")
    other_user = CurrentUser(user_id="other-user")

    workspace_projects.create_workspace(
        current_user=owner,
        workspace_id="ws-owner",
        name="Owner Workspace",
    )

    workspace_projects.create_project(
        current_user=owner,
        project_id="project-owner",
        workspace_id="ws-owner",
        name="Owner Project",
    )

    plan = ExecutionPlan(
        steps=(),
        version="1.0",
        metadata={},
    )

    authoring_service.save_workflow(
        current_user=owner,
        workflow_id="wf-owner",
        project_id="project-owner",
        name="Owner Workflow",
        version="1.0",
        plan=plan,
    )

    versions = authoring_service.list_workflow_versions(
        current_user=other_user,
        workflow_id="wf-owner",
    )

    assert versions == []

def test_other_user_cannot_activate_workflow_version():
    workspace_projects, authoring_service = build_services()

    owner = CurrentUser(user_id="owner")
    other_user = CurrentUser(user_id="other-user")

    workspace_projects.create_workspace(
        current_user=owner,
        workspace_id="ws-owner",
        name="Owner Workspace",
    )

    workspace_projects.create_project(
        current_user=owner,
        project_id="project-owner",
        workspace_id="ws-owner",
        name="Owner Project",
    )

    plan_v1 = ExecutionPlan(
        steps=(),
        version="1.0",
        metadata={},
    )

    authoring_service.save_workflow(
        current_user=owner,
        workflow_id="wf-owner",
        project_id="project-owner",
        name="Owner Workflow",
        version="1.0",
        plan=plan_v1,
    )

    plan_v2 = ExecutionPlan(
        steps=(),
        version="2.0",
        metadata={},
    )

    authoring_service.create_workflow_version(
        current_user=owner,
        workflow_id="wf-owner",
        version="2.0",
        plan=plan_v2,
    )

    with pytest.raises(
        ValueError,
        match="Workflow not found",
    ):
        authoring_service.activate_workflow_version(
            current_user=other_user,
            workflow_id="wf-owner",
            version="2.0",
        )

    workflow = authoring_service.get_workflow(
        current_user=owner,
        workflow_id="wf-owner",
    )

    assert workflow is not None
    assert workflow.active_version == "1.0"