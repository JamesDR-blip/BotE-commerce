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
        owner_id="user-1",
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
        owner_id="user-1",
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

def test_workspace_repository_scopes_by_owner():

    repo = WorkspaceRepository(
        create_session()
    )

    repo.create(
        workspace_id="ws-1",
        owner_id="user-1",
        name="User 1 Workspace",
    )

    repo.create(
        workspace_id="ws-2",
        owner_id="user-2",
        name="User 2 Workspace",
    )

    assert repo.get_for_owner(
        workspace_id="ws-1",
        owner_id="user-1",
    ) is not None

    assert repo.get_for_owner(
        workspace_id="ws-1",
        owner_id="user-2",
    ) is None

    assert [
        item.id
        for item in repo.list_for_owner("user-1")
    ] == ["ws-1"]

def test_workspace_repository_scopes_by_organization():

    repo = WorkspaceRepository(
        create_session()
    )

    repo.create(
        workspace_id="ws-org-1",
        owner_id="user-1",
        organization_id="org-1",
        name="Org 1 Workspace",
    )

    repo.create(
        workspace_id="ws-org-2",
        owner_id="user-1",
        organization_id="org-2",
        name="Org 2 Workspace",
    )

    assert repo.get_for_organization(
        workspace_id="ws-org-1",
        organization_id="org-1",
    ) is not None

    assert repo.get_for_organization(
        workspace_id="ws-org-1",
        organization_id="org-2",
    ) is None

    assert repo.list_for_organization(
        "org-1"
    )[0].id == "ws-org-1"


def test_workspace_repository_combines_owner_and_organization_scope():

    repo = WorkspaceRepository(
        create_session()
    )

    repo.create(
        workspace_id="ws-1",
        owner_id="user-1",
        organization_id="org-1",
        name="Workspace",
    )

    assert repo.get_for_owner_in_organization(
        workspace_id="ws-1",
        owner_id="user-1",
        organization_id="org-1",
    ) is not None

    assert repo.get_for_owner_in_organization(
        workspace_id="ws-1",
        owner_id="user-2",
        organization_id="org-1",
    ) is None

    assert repo.get_for_owner_in_organization(
        workspace_id="ws-1",
        owner_id="user-1",
        organization_id="org-2",
    ) is None
def test_project_repository_scopes_by_organization():

    sessions = create_session()

    workspace_repo = WorkspaceRepository(sessions)
    workspace_repo.create(
        workspace_id="ws-org-1",
        owner_id="user-1",
        organization_id="org-1",
        name="Org 1 Workspace",
    )

    workspace_repo.create(
        workspace_id="ws-org-2",
        owner_id="user-2",
        organization_id="org-2",
        name="Org 2 Workspace",
    )

    repo = ProjectRepository(sessions)

    repo.create(
        project_id="p-org-1",
        workspace_id="ws-org-1",
        name="Org 1 Project",
    )

    repo.create(
        project_id="p-org-2",
        workspace_id="ws-org-2",
        name="Org 2 Project",
    )

    assert repo.get_for_organization(
        project_id="p-org-1",
        organization_id="org-1",
    ) is not None

    assert repo.get_for_organization(
        project_id="p-org-1",
        organization_id="org-2",
    ) is None

    assert repo.get_for_owner_in_organization(
        project_id="p-org-1",
        owner_id="user-1",
        organization_id="org-1",
    ) is not None

    assert repo.get_for_owner_in_organization(
        project_id="p-org-1",
        owner_id="user-2",
        organization_id="org-1",
    ) is None


def test_dataset_repository_scopes_by_organization():

    sessions = create_session()

    workspace_repo = WorkspaceRepository(sessions)
    workspace_repo.create(
        workspace_id="ws-org-1",
        owner_id="user-1",
        organization_id="org-1",
        name="Org 1 Workspace",
    )

    workspace_repo.create(
        workspace_id="ws-org-2",
        owner_id="user-2",
        organization_id="org-2",
        name="Org 2 Workspace",
    )

    project_repo = ProjectRepository(sessions)
    project_repo.create(
        project_id="p-org-1",
        workspace_id="ws-org-1",
        name="Org 1 Project",
    )

    project_repo.create(
        project_id="p-org-2",
        workspace_id="ws-org-2",
        name="Org 2 Project",
    )

    repo = DatasetRepository(sessions)

    repo.create(
        dataset_id="d-org-1",
        project_id="p-org-1",
        name="Org 1 Dataset",
        source_type="upload",
        metadata={},
    )

    repo.create(
        dataset_id="d-org-2",
        project_id="p-org-2",
        name="Org 2 Dataset",
        source_type="upload",
        metadata={},
    )

    assert repo.get_for_organization(
        dataset_id="d-org-1",
        organization_id="org-1",
    ) is not None

    assert repo.get_for_organization(
        dataset_id="d-org-1",
        organization_id="org-2",
    ) is None

    assert repo.get_for_owner_in_organization(
        dataset_id="d-org-1",
        owner_id="user-1",
        organization_id="org-1",
    ) is not None

    assert repo.get_for_owner_in_organization(
        dataset_id="d-org-1",
        owner_id="user-2",
        organization_id="org-1",
    ) is None

    assert [
        item.id
        for item in repo.list_by_project_for_organization(
            project_id="p-org-1",
            organization_id="org-1",
        )
    ] == ["d-org-1"]

    assert repo.list_by_project_for_organization(
        project_id="p-org-1",
        organization_id="org-2",
    ) == []


def test_workflow_repository_scopes_by_organization():

    sessions = create_session()

    workspace_repo = WorkspaceRepository(sessions)
    workspace_repo.create(
        workspace_id="ws-org-1",
        owner_id="user-1",
        organization_id="org-1",
        name="Org 1 Workspace",
    )

    workspace_repo.create(
        workspace_id="ws-org-2",
        owner_id="user-2",
        organization_id="org-2",
        name="Org 2 Workspace",
    )

    project_repo = ProjectRepository(sessions)
    project_repo.create(
        project_id="p-org-1",
        workspace_id="ws-org-1",
        name="Org 1 Project",
    )

    project_repo.create(
        project_id="p-org-2",
        workspace_id="ws-org-2",
        name="Org 2 Project",
    )

    repo = WorkflowRepository(sessions)

    repo.create(
        workflow_id="wf-org-1",
        project_id="p-org-1",
        name="Org 1 Workflow",
        version="1.0",
        plan_json="{}",
    )

    repo.create(
        workflow_id="wf-org-2",
        project_id="p-org-2",
        name="Org 2 Workflow",
        version="1.0",
        plan_json="{}",
    )

    assert repo.get_for_organization(
        workflow_id="wf-org-1",
        organization_id="org-1",
    ) is not None

    assert repo.get_for_organization(
        workflow_id="wf-org-1",
        organization_id="org-2",
    ) is None

    assert repo.get_for_owner_in_organization(
        workflow_id="wf-org-1",
        owner_id="user-1",
        organization_id="org-1",
    ) is not None

    assert repo.get_for_owner_in_organization(
        workflow_id="wf-org-1",
        owner_id="user-2",
        organization_id="org-1",
    ) is None

    assert [
        item.id
        for item in repo.list_by_project_for_organization(
            project_id="p-org-1",
            organization_id="org-1",
        )
    ] == ["wf-org-1"]

    assert repo.list_by_project_for_organization(
        project_id="p-org-1",
        organization_id="org-2",
    ) == []


def test_workflow_version_repository_scopes_by_organization():

    sessions = create_session()

    workspace_repo = WorkspaceRepository(sessions)
    workspace_repo.create(
        workspace_id="ws-org-1",
        owner_id="user-1",
        organization_id="org-1",
        name="Org 1 Workspace",
    )

    project_repo = ProjectRepository(sessions)
    project_repo.create(
        project_id="p-org-1",
        workspace_id="ws-org-1",
        name="Org 1 Project",
    )

    repo = WorkflowRepository(sessions)

    repo.create(
        workflow_id="wf-org-1",
        project_id="p-org-1",
        name="Org 1 Workflow",
        version="1.0",
        plan_json="{}",
    )

    repo.create_version(
        workflow_id="wf-org-1",
        version="2.0",
        plan_json='{"step": "validate"}',
    )

    versions = repo.list_versions_for_organization(
        workflow_id="wf-org-1",
        organization_id="org-1",
    )

    assert [version.version for version in versions] == [
        "1.0",
        "2.0",
    ]

    assert repo.get_version_for_organization(
        workflow_id="wf-org-1",
        version="2.0",
        organization_id="org-1",
    ) is not None

    assert repo.get_version_for_organization(
        workflow_id="wf-org-1",
        version="2.0",
        organization_id="org-2",
    ) is None

    assert [
        version.version
        for version in repo.list_versions_for_owner_in_organization(
            workflow_id="wf-org-1",
            owner_id="user-1",
            organization_id="org-1",
        )
    ] == ["1.0", "2.0"]

    assert repo.list_versions_for_owner_in_organization(
        workflow_id="wf-org-1",
        owner_id="user-1",
        organization_id="org-2",
    ) == []
