from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from application.changesets.mutation_service import ChangeSetMutationService
from database.models import (
    Base,
    CompliancePolicyRecord,
    DatasetRecord,
    OrganizationRecord,
    ProjectRecord,
    UserRecord,
    WorkspaceRecord,
)
from domain.changeset import ChangeSet, ChangeSetStatus
from domain.exceptions import ComplianceViolationError
from repositories.changesets import ChangeSetRepository
from repositories.compliance_policies import CompliancePolicyRepository
from services.compliance import ComplianceService


def create_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


class FakeDatasetStorage:
    def __init__(self):
        self.contents = {
            "datasets/dataset-1/before.csv": b"before-artifact",
            "datasets/dataset-1/after.csv": b"after-artifact",
        }

    def open(self, *, storage_key: str):
        return BytesIO(self.contents[storage_key])

def make_changeset() -> ChangeSet:
    return ChangeSet(
        id="cs-1",
        dataset_id="dataset-1",
        execution_id="execution-1",
        workflow_id="workflow-1",
        workflow_version="1.0",
        before_storage_key="datasets/dataset-1/before.csv",
        before_content_hash=sha256(b"before-artifact").hexdigest(),
        after_storage_key="datasets/dataset-1/after.csv",
        after_content_hash=sha256(b"after-artifact").hexdigest(),
        status=ChangeSetStatus.PREPARED,
        created_at=datetime.now(timezone.utc),
    )


def seed_governed_changeset(sessions):
    with sessions() as session:
        session.add(
            UserRecord(
                id="user-1",
                email="test@example.com",
                display_name="Test User",
            )
        )
        session.add(
            OrganizationRecord(
                id="org-1",
                name="Test Organization",
            )
        )
        session.add(
            WorkspaceRecord(
                id="workspace-1",
                owner_id="user-1",
                organization_id="org-1",
                name="test-workspace",
            )
        )
        session.add(
            ProjectRecord(
                id="project-1",
                workspace_id="workspace-1",
                name="test-project",
            )
        )
        session.add(
            DatasetRecord(
                id="dataset-1",
                project_id="project-1",
                name="catalog.csv",
                source_type="upload",
                status="READY",
                storage_key="datasets/dataset-1/before.csv",
                content_hash="b" * 64,
            )
        )
        session.commit()


def test_matching_compliance_policy_blocks_changeset_application():
    sessions = create_session()
    changesets = ChangeSetRepository(sessions)

    seed_governed_changeset(sessions)
    changesets.create(make_changeset(), [])

    policies = CompliancePolicyRepository(sessions)
    policies.save(
        __import__("domain.compliance", fromlist=["CompliancePolicy"]).CompliancePolicy(
            id="policy-1",
            organization_id="org-1",
            name="governed-workflow",
            resource="changeset",
            action="apply",
            condition={"workflow_id": "workflow-1"},
            reason="This workflow requires governed approval.",
        )
    )

    compliance = ComplianceService(policies=policies)
    service = ChangeSetMutationService(
        sessions=sessions,
        changesets=changesets,
        dataset_storage=FakeDatasetStorage(),
        compliance_service=compliance,
    )

    with pytest.raises(ComplianceViolationError) as exc_info:
        service.apply(changeset_id="cs-1", actor_id="user-1")

    assert exc_info.value.organization_id == "org-1"
    assert exc_info.value.resource == "changeset"
    assert exc_info.value.action == "apply"

    loaded = changesets.get("cs-1")
    assert loaded is not None
    assert loaded.status is ChangeSetStatus.PREPARED

    with sessions() as session:
        dataset = session.get(DatasetRecord, "dataset-1")
        assert dataset is not None
        assert dataset.storage_key == (
            "datasets/dataset-1/before.csv"
        )
        assert dataset.content_hash == "b" * 64


def test_non_matching_compliance_policy_allows_changeset_application():
    sessions = create_session()
    changesets = ChangeSetRepository(sessions)

    seed_governed_changeset(sessions)
    changesets.create(make_changeset(), [])

    policies = CompliancePolicyRepository(sessions)
    policies.save(
        __import__("domain.compliance", fromlist=["CompliancePolicy"]).CompliancePolicy(
            id="policy-1",
            organization_id="org-1",
            name="other-workflow",
            resource="changeset",
            action="apply",
            condition={"workflow_id": "other-workflow"},
            reason="Only another workflow is restricted.",
        )
    )

    compliance = ComplianceService(policies=policies)
    service = ChangeSetMutationService(
        sessions=sessions,
        changesets=changesets,
        dataset_storage=FakeDatasetStorage(),
        compliance_service=compliance,
    )

    applied = service.apply(changeset_id="cs-1", actor_id="user-1")

    assert applied.status is ChangeSetStatus.APPLIED

    with sessions() as session:
        dataset = session.get(DatasetRecord, "dataset-1")
        assert dataset is not None
        assert dataset.storage_key == (
            "datasets/dataset-1/after.csv"
        )
        assert dataset.content_hash == sha256(b"after-artifact").hexdigest()
