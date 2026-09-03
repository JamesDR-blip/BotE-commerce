from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base

from repositories.workspaces import WorkspaceRepository
from repositories.projects import ProjectRepository
from repositories.datasets import DatasetRepository
from repositories.workflows import WorkflowRepository

from services.studio_service import StudioService

from domain.plans import ExecutionPlan
from domain.identity import CurrentUser


def build_service():
    engine = create_engine("sqlite://")

    Base.metadata.create_all(engine)

    sessions = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    return StudioService(
        workspaces=WorkspaceRepository(sessions),
        projects=ProjectRepository(sessions),
        datasets=DatasetRepository(sessions),
        workflows=WorkflowRepository(sessions),
    )


def test_workflow_versions_are_immutable_snapshots():
    service = build_service()
    current_user = CurrentUser(
        user_id="test-user"
    )

    service.create_workspace(
        current_user=current_user,
        workspace_id="ws-1",
        name="Demo",
    )

    service.create_project(
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

    service.save_workflow(
        workflow_id="wf-1",
        project_id="p-1",
        name="Validation",
        version="1.0",
        plan=plan_v1,
    )

    v1_before = service.get_workflow_version(
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

    service.create_workflow_version(
        workflow_id="wf-1",
        version="2.0",
        plan=plan_v2,
    )

    service.activate_workflow_version(
        "wf-1",
        "2.0",
    )

    v1_after = service.get_workflow_version(
        workflow_id="wf-1",
        version="1.0",
    )

    v2 = service.get_workflow_version(
        workflow_id="wf-1",
        version="2.0",
    )

    assert v1_after is not None
    assert v2 is not None

    assert v1_after.plan_json == original_v1_plan
    assert v2.plan_json != v1_after.plan_json

    workflow = service.get_workflow("wf-1")

    assert workflow is not None
    assert workflow.active_version == "2.0"