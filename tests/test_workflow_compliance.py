import pytest

from application.workflows.runtime_service import WorkflowRuntimeService
from domain.compliance import CompliancePolicy
from domain.exceptions import ComplianceViolationError
from domain.identity import CurrentUser
from services.compliance import ComplianceService

from tests.test_workflow_runtime_service import (
    FakeEngine,
    FakeQueuedEngine,
    FakeWorkflowQueue,
    FakeWorkflowRepository,
)


class BlockingCompliance:
    def __init__(self):
        self.calls = []

    def check(self, **kwargs):
        self.calls.append(kwargs)
        raise ComplianceViolationError(
            organization_id=kwargs["organization_id"],
            resource=kwargs["resource"],
            action=kwargs["action"],
            reason="Workflow execution is restricted.",
        )


class GovernedProjectRepository:
    class Project:
        workspace_id = "workspace-1"

    def get_for_owner(self, *, project_id, owner_id):
        assert project_id == "project-1"
        assert owner_id == "user-1"
        return self.Project()


class GovernedWorkspaceRepository:
    class Workspace:
        organization_id = "org-1"

    def get_for_owner(self, *, workspace_id, owner_id):
        assert workspace_id == "workspace-1"
        assert owner_id == "user-1"
        return self.Workspace()


class GovernedAuthorization:
    def authorize(self, **kwargs):
        assert kwargs["organization_id"] == "org-1"


def test_workflow_compliance_blocks_sync_execution_before_engine():
    engine = FakeEngine()
    compliance = BlockingCompliance()

    service = WorkflowRuntimeService(
        workflow_engine=lambda: engine,
        workflow_history=lambda: None,
        workflows=lambda: FakeWorkflowRepository(),
        projects=lambda: GovernedProjectRepository(),
        workspaces=lambda: GovernedWorkspaceRepository(),
        authorization=GovernedAuthorization(),
        compliance_service=lambda: compliance,
    )

    with pytest.raises(ComplianceViolationError):
        service.execute(
            current_user=CurrentUser(user_id="user-1"),
            workflow_id="workflow-1",
            inputs={"source": "catalog"},
            dataset_id="dataset-1",
        )

    assert compliance.calls == [
        {
            "organization_id": "org-1",
            "resource": "workflow",
            "action": "execute",
            "context": {
                "workflow_id": "workflow-1",
                "dataset_id": "dataset-1",
            },
        }
    ]
    assert engine.calls == []


def test_workflow_compliance_blocks_async_execution_before_queue():
    engine = FakeQueuedEngine()
    queue = FakeWorkflowQueue()
    compliance = BlockingCompliance()

    service = WorkflowRuntimeService(
        workflow_engine=lambda: engine,
        workflow_history=lambda: None,
        workflows=lambda: FakeWorkflowRepository(),
        projects=lambda: GovernedProjectRepository(),
        workspaces=lambda: GovernedWorkspaceRepository(),
        authorization=GovernedAuthorization(),
        workflow_queue=lambda: queue,
        compliance_service=lambda: compliance,
    )

    with pytest.raises(ComplianceViolationError):
        service.execute_async(
            current_user=CurrentUser(user_id="user-1"),
            workflow_id="workflow-1",
            inputs={"source": "catalog"},
            dataset_id="dataset-1",
        )

    assert compliance.calls == [
        {
            "organization_id": "org-1",
            "resource": "workflow",
            "action": "execute",
            "context": {
                "workflow_id": "workflow-1",
                "dataset_id": "dataset-1",
            },
        }
    ]
    assert engine.executions == {}
    assert queue.dispatched == []


def test_workflow_compliance_allows_non_matching_policy():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from database.models import Base
    from repositories.compliance_policies import CompliancePolicyRepository

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)

    policies = CompliancePolicyRepository(sessions)
    policies.save(
        CompliancePolicy(
            id="policy-1",
            organization_id="org-1",
            name="other-workflow",
            resource="workflow",
            action="execute",
            condition={"workflow_id": "other-workflow"},
            reason="Only another workflow is restricted.",
        )
    )

    compliance = ComplianceService(policies=policies)
    runtime_engine = FakeEngine()

    service = WorkflowRuntimeService(
        workflow_engine=lambda: runtime_engine,
        workflow_history=lambda: None,
        workflows=lambda: FakeWorkflowRepository(),
        projects=lambda: GovernedProjectRepository(),
        workspaces=lambda: GovernedWorkspaceRepository(),
        authorization=GovernedAuthorization(),
        compliance_service=lambda: compliance,
    )

    result = service.execute(
        current_user=CurrentUser(user_id="user-1"),
        workflow_id="workflow-1",
        inputs={"source": "catalog"},
    )

    assert result == "runtime"
    assert runtime_engine.calls
