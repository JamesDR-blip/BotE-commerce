from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from domain.exceptions import QuotaExceededError
from domain.quota import QuotaDimension
from repositories.datasets import DatasetRepository
from repositories.projects import ProjectRepository
from repositories.quotas import QuotaRepository
from repositories.workflow_executions import WorkflowExecutionRepository
from repositories.workspaces import WorkspaceRepository
from services.quota import QuotaService


def make_repositories():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)

    return (
        sessions,
        QuotaRepository(sessions),
        WorkspaceRepository(sessions),
        ProjectRepository(sessions),
        DatasetRepository(sessions),
        WorkflowExecutionRepository(sessions),
    )


def seed_tenant_data():
    (
        sessions,
        quota_repo,
        workspace_repo,
        project_repo,
        dataset_repo,
        execution_repo,
    ) = make_repositories()

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

    dataset_repo.create(
        dataset_id="d-org-1",
        project_id="p-org-1",
        name="Org 1 Dataset",
        source_type="upload",
        metadata={},
        size_bytes=100,
    )
    dataset_repo.create(
        dataset_id="d-org-2",
        project_id="p-org-2",
        name="Org 2 Dataset",
        source_type="upload",
        metadata={},
        size_bytes=250,
    )

    execution_repo.create(
        execution_id="e-org-1",
        workflow_id="wf-org-1",
        workflow_version="v1",
    )

    return (
        sessions,
        quota_repo,
        workspace_repo,
        project_repo,
        dataset_repo,
        execution_repo,
    )


def test_quota_repository_scopes_usage_by_organization():
    _, quota_repo, _, _, _, _ = seed_tenant_data()

    assert quota_repo.get_usage(
        organization_id="org-1",
        dimension=QuotaDimension.STORAGE_BYTES,
    ) == 100

    assert quota_repo.get_usage(
        organization_id="org-2",
        dimension=QuotaDimension.STORAGE_BYTES,
    ) == 250

    assert quota_repo.get_usage(
        organization_id="org-1",
        dimension=QuotaDimension.DATASET_COUNT,
    ) == 1

    assert quota_repo.get_usage(
        organization_id="org-2",
        dimension=QuotaDimension.DATASET_COUNT,
    ) == 1


def test_quota_repository_set_and_update():
    _, quota_repo, _, _, _, _ = make_repositories()

    created = quota_repo.set_quota(
        quota_id="quota-1",
        organization_id="org-1",
        dimension=QuotaDimension.DATASET_COUNT,
        limit=3,
    )

    assert created.limit == 3
    assert quota_repo.get_quota(
        organization_id="org-1",
        dimension=QuotaDimension.DATASET_COUNT,
    ).limit == 3

    updated = quota_repo.set_quota(
        quota_id="quota-ignored",
        organization_id="org-1",
        dimension=QuotaDimension.DATASET_COUNT,
        limit=5,
    )

    assert updated.id == "quota-1"
    assert updated.limit == 5


def test_quota_service_allows_unlimited_dimension():
    _, quota_repo, _, _, _, _ = make_repositories()
    service = QuotaService(quotas=quota_repo)

    service.check(
        organization_id="org-1",
        dimension=QuotaDimension.DATASET_COUNT,
        requested_usage=1,
    )


def test_quota_service_allows_within_limit():
    _, quota_repo, _, _, _, _ = seed_tenant_data()
    quota_repo.set_quota(
        quota_id="quota-1",
        organization_id="org-1",
        dimension=QuotaDimension.STORAGE_BYTES,
        limit=150,
    )

    QuotaService(quotas=quota_repo).check(
        organization_id="org-1",
        dimension=QuotaDimension.STORAGE_BYTES,
        requested_usage=50,
    )


def test_quota_service_denies_when_projected_usage_exceeds_limit():
    _, quota_repo, _, _, _, _ = seed_tenant_data()
    quota_repo.set_quota(
        quota_id="quota-1",
        organization_id="org-1",
        dimension=QuotaDimension.STORAGE_BYTES,
        limit=100,
    )

    try:
        QuotaService(quotas=quota_repo).check(
            organization_id="org-1",
            dimension=QuotaDimension.STORAGE_BYTES,
            requested_usage=1,
        )
    except QuotaExceededError as exc:
        assert exc.dimension == "STORAGE_BYTES"
        assert exc.current_usage == 100
        assert exc.requested_usage == 1
        assert exc.limit == 100
    else:
        raise AssertionError("Expected QuotaExceededError")


def test_workflow_execution_usage_is_organization_scoped():
    (
        sessions,
        quota_repo,
        workspace_repo,
        project_repo,
        _,
        execution_repo,
    ) = make_repositories()

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

    from database.models import WorkflowRecord

    with sessions() as session:
        session.add_all(
            [
                WorkflowRecord(
                    id="wf-org-1",
                    project_id="p-org-1",
                    name="Org 1 Workflow",
                ),
                WorkflowRecord(
                    id="wf-org-2",
                    project_id="p-org-2",
                    name="Org 2 Workflow",
                ),
            ]
        )
        session.commit()

    execution_repo.create(
        execution_id="e-org-1",
        workflow_id="wf-org-1",
        workflow_version="v1",
    )
    execution_repo.create(
        execution_id="e-org-2",
        workflow_id="wf-org-2",
        workflow_version="v1",
    )

    assert quota_repo.get_usage(
        organization_id="org-1",
        dimension=QuotaDimension.WORKFLOW_EXECUTION_COUNT,
    ) == 1

    assert quota_repo.get_usage(
        organization_id="org-2",
        dimension=QuotaDimension.WORKFLOW_EXECUTION_COUNT,
    ) == 1
