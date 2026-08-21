from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base

from repositories.workspaces import WorkspaceRepository
from repositories.projects import ProjectRepository
from repositories.datasets import DatasetRepository
from repositories.workflows import WorkflowRepository

from services.studio_service import StudioService

from domain.plans import ExecutionPlan


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


def test_studio_workflow_lifecycle():
    service = build_service()

    service.create_workspace(
        workspace_id="ws-1",
        name="Demo",
    )

    service.create_project(
        project_id="p-1",
        workspace_id="ws-1",
        name="Catalog",
    )

    plan_v1 = ExecutionPlan(
        steps=(),
        version="1.0",
        metadata={},
    )

    workflow = service.save_workflow(
        workflow_id="wf-1",
        project_id="p-1",
        name="Validation",
        version="1.0",
        plan=plan_v1,
    )

    assert workflow.id == "wf-1"

    loaded = service.get_workflow("wf-1")

    assert loaded is not None
    assert loaded.name == "Validation"
    assert loaded.active_version == "1.0"

    workflows = service.list_workflows("p-1")

    assert len(workflows) == 1
    assert workflows[0].id == "wf-1"

    plan_v2 = ExecutionPlan(
        steps=(),
        version="2.0",
        metadata={
            "description": "Improved validation"
        },
    )

    version = service.create_workflow_version(
        workflow_id="wf-1",
        version="2.0",
        plan=plan_v2,
    )

    assert version.version == "2.0"

    versions = service.list_workflow_versions("wf-1")

    assert len(versions) == 2

    loaded_v2 = service.get_workflow_version(
        workflow_id="wf-1",
        version="2.0",
    )

    assert loaded_v2 is not None
    assert loaded_v2.version == "2.0"

    activated = service.activate_workflow_version(
        "wf-1",
        "2.0",
    )

    assert activated.active_version == "2.0"

    active = service.workflows.get_active_version(
        "wf-1"
    )

    assert active is not None
    assert active.version == "2.0"