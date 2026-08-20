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

    engine = create_engine(
        "sqlite://"
    )

    Base.metadata.create_all(engine)

    sessions = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    return StudioService(
        workspaces=WorkspaceRepository(
            sessions
        ),
        projects=ProjectRepository(
            sessions
        ),
        datasets=DatasetRepository(
            sessions
        ),
        workflows=WorkflowRepository(
            sessions
        ),
    )



def test_create_workspace_project_dataset():

    service = build_service()


    service.create_workspace(
        workspace_id="ws-1",
        name="Demo",
    )


    project = service.create_project(
        project_id="p-1",
        workspace_id="ws-1",
        name="Catalog",
    )


    dataset = service.create_dataset(
        dataset_id="d-1",
        project_id=project.id,
        name="catalog.csv",
        source_type="upload",
        metadata={
            "rows":1000
        },
    )


    assert dataset.name == "catalog.csv"



def test_save_workflow():

    service = build_service()


    plan = ExecutionPlan(
        steps=(),
        version="1.0",
        metadata={},
    )


    workflow = service.save_workflow(
        workflow_id="wf-1",
        project_id="p-1",
        name="Validation",
        version="1",
        plan=plan,
    )


    assert workflow.active_version == "1"