from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base

from repositories.workspaces import WorkspaceRepository
from repositories.projects import ProjectRepository
from repositories.datasets import DatasetRepository
from repositories.workflows import WorkflowRepository



def create_session():
    engine = create_engine(
        "sqlite://"
    )

    Base.metadata.create_all(engine)

    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )



def test_workspace_repository():

    repo = WorkspaceRepository(
        create_session()
    )

    item = repo.create(
        workspace_id="ws-1",
        name="Demo",
    )

    assert item.id == "ws-1"

    loaded = repo.get("ws-1")

    assert loaded.name == "Demo"



def test_project_repository():

    workspace_repo = WorkspaceRepository(
        create_session()
    )

    workspace_repo.create(
        workspace_id="ws-1",
        name="Demo",
    )

    repo = ProjectRepository(
        create_session()
    )

    item = repo.create(
        project_id="p-1",
        workspace_id="ws-1",
        name="Catalog",
    )

    assert item.workspace_id == "ws-1"



def test_dataset_repository():

    repo = DatasetRepository(
        create_session()
    )

    item = repo.create(
        dataset_id="d-1",
        project_id="p-1",
        name="catalog.csv",
        source_type="upload",
        metadata={
            "rows":100
        },
    )

    assert item.metadata_json["rows"] == 100



def test_workflow_repository():

    repo = WorkflowRepository(
        create_session()
    )

    item = repo.create(
        workflow_id="wf-1",
        project_id="p-1",
        name="Validation",
        version="1.0",
        plan_json="{}",
    )

    version = repo.get_version(
        "wf-1",
        "1.0",
    )

    assert item.id == "wf-1"
    assert item.project_id == "p-1"
    assert item.name == "Validation"
    assert item.active_version == "1.0"
    assert item.status == "DRAFT"

    assert version is not None
    assert version.workflow_id == "wf-1"
    assert version.version == "1.0"
    assert version.plan_json == "{}"