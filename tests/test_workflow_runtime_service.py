import pytest
from application.workflows.runtime_service import WorkflowRuntimeService
from domain.approval import ApprovalRequest
from domain.identity import CurrentUser
from domain.exceptions import QuotaExceededError
from domain.quota import QuotaDimension


class FakeEngine:
    def __init__(self) -> None:
        self.calls = []

    def execute(self, **kwargs):
        self.calls.append(kwargs)
        return "runtime"


class FakeHistory:
    def get_workflow_execution_detail(self, execution_id):
        return {"execution_id": execution_id}


class FakeWorkflow:
    project_id = "project-1"


class FakeWorkflowRepository:
    def get_for_owner(self, *, workflow_id, owner_id):
        return FakeWorkflow()


def test_runtime_service_delegates_execution_with_a_generated_id():
    engine = FakeEngine()
    service = WorkflowRuntimeService(
        workflow_engine=lambda: engine,
        workflow_history=FakeHistory,
        workflows=lambda: FakeWorkflowRepository(),
    )

    result = service.execute(
        current_user=CurrentUser(user_id="user-1"),
        workflow_id="workflow-1",
        inputs={"source": "catalog"},
    )

    assert result == "runtime"
    assert engine.calls[0]["workflow_id"] == "workflow-1"
    assert engine.calls[0]["inputs"] == {"source": "catalog"}
    assert engine.calls[0]["execution_id"]


def test_runtime_service_delegates_history_lookup():
    service = WorkflowRuntimeService(
        workflow_engine=FakeEngine,
        workflow_history=FakeHistory,
    )

    assert service.get_execution_detail("execution-1") == {
        "execution_id": "execution-1"
    }

from domain.plans import ExecutionPlan
from domain.studio.runtime import WorkflowExecution
from domain.workflow_execution_status import WorkflowExecutionStatus


class FakeQueuedEngine:
    def __init__(self):
        self.executions = {}
        self.executed = []

    def create_queued(self, **kwargs):
        execution = WorkflowExecution(
            execution_id=kwargs["execution_id"],
            workflow_id=kwargs["workflow_id"],
            workflow_version="1.0",
            plan=kwargs["plan"],
            inputs=kwargs["inputs"],
            status=WorkflowExecutionStatus.QUEUED,
        )
        self.executions[execution.execution_id] = execution
        return execution

    def execute_existing(self, execution_id):
        self.executed.append(execution_id)
        return self.executions[execution_id].start().complete({})

    def execute(self, **kwargs):
        raise AssertionError("legacy execute path must not be used")


class FakeWorkflowRepository:
    class Workflow:
        project_id = "project-1"

    def get_for_owner(self, *, workflow_id, owner_id):
        return self.Workflow()


class FakeDatasetRepository:
    class Dataset:
        project_id = "project-1"

    def get_for_owner(self, *, dataset_id, owner_id):
        return self.Dataset()


class FakeWorkflowQueue:
    def __init__(self):
        self.dispatched = []

    def dispatch(self, execution_id):
        self.dispatched.append(execution_id)


class FakeExecutions:
    def __init__(self):
        self.pending = []
        self.running = []

    def mark_pending_approval(self, execution_id):
        self.pending.append(execution_id)

    def mark_running(self, execution_id):
        self.running.append(execution_id)


class FakeRiskAssessments:
    def __init__(self):
        self.created = []

    def create(self, **kwargs):
        self.created.append(kwargs)


class FakeRiskService:
    class Result:
        class Score:
            value = "HIGH"

        class Confidence:
            value = 0.75

        risk_score = Score()
        confidence = Confidence()
        approval_required = True

    def evaluate(self, *, blast_radius, confidence):
        assert blast_radius == 0.8
        assert confidence == 0.75
        return self.Result()


class FakeHealth:
    class Score:
        confidence_score = 0.75

    def get_health(self, *, dataset_id, owner_id):
        return self.Score()


class FakeChangeSet:
    def __init__(self, changeset_id="changeset-1"):
        self.id = changeset_id


class FakeChangeSetService:
    def __init__(self):
        self.calls = []

    def prepare_candidate(self, *, execution_id):
        self.calls.append(execution_id)
        return FakeChangeSet()


class FakeApprovalService:
    def __init__(self):
        self.requests = []

    def request_approval(self, request):
        assert isinstance(request, ApprovalRequest)
        self.requests.append(request)
        return "test-approval-token"


def test_runtime_high_risk_enters_pending_approval():
    from application.workflows.runtime_service import WorkflowRuntimeService
    from domain.identity import CurrentUser

    engine = FakeQueuedEngine()
    executions = FakeExecutions()
    assessments = FakeRiskAssessments()

    plan = ExecutionPlan(
        steps=(),
        metadata={
            "risk": {
                "blast_radius": 0.8,
            }
        },
    )

    engine_plan = plan

    class Engine(FakeQueuedEngine):
        def create_queued(self, **kwargs):
            kwargs["plan"] = engine_plan
            return super().create_queued(**kwargs)

    engine = Engine()
    changesets = FakeChangeSetService()
    approvals = FakeApprovalService()

    service = WorkflowRuntimeService(
        workflow_engine=lambda: engine,
        workflow_history=lambda: None,
        workflows=lambda: FakeWorkflowRepository(),
        datasets=lambda: FakeDatasetRepository(),
        data_health=lambda: FakeHealth(),
        workflow_queue=lambda: FakeWorkflowQueue(),
        risk_service=lambda: FakeRiskService(),
        risk_assessments=lambda: assessments,
        workflow_executions=lambda: executions,
        changeset_service=lambda: changesets,
        approval_service=lambda: approvals,
    )

    result = service.execute_async(
        current_user=CurrentUser(user_id="user-1"),
        workflow_id="workflow-1",
        inputs={},
        dataset_id="dataset-1",
    )

    assert result.status == WorkflowExecutionStatus.PENDING_APPROVAL
    assert result.changeset_id == "changeset-1"
    assert changesets.calls == [result.execution_id]
    assert executions.pending == [result.execution_id]
    assert executions.running == []
    assert engine.executed == []
    assert assessments.created[0]["risk_score"] == "HIGH"
    assert assessments.created[0]["confidence_score"] == 0.75
    assert assessments.created[0]["approval_required"] is True

    assert len(approvals.requests) == 1

    approval = approvals.requests[0]
    assert approval.execution_id == result.execution_id
    assert approval.changeset_id == "changeset-1"
    assert approval.risk_score == "HIGH"
    assert approval.confidence_score == 0.75
    assert approval.requested_by == "user-1"
    assert approval.created_at is not None
    assert approval.created_at.tzinfo is not None


def test_runtime_sync_high_risk_creates_approval_request():
    from application.workflows.runtime_service import WorkflowRuntimeService
    from domain.identity import CurrentUser

    plan = ExecutionPlan(
        steps=(),
        metadata={
            "risk": {
                "blast_radius": 0.8,
            },
        },
    )

    class Engine(FakeQueuedEngine):
        def create_queued(self, **kwargs):
            kwargs["plan"] = plan
            return super().create_queued(**kwargs)

    engine = Engine()
    executions = FakeExecutions()
    assessments = FakeRiskAssessments()
    changesets = FakeChangeSetService()
    approvals = FakeApprovalService()

    service = WorkflowRuntimeService(
        workflow_engine=lambda: engine,
        workflow_history=lambda: None,
        workflows=lambda: FakeWorkflowRepository(),
        datasets=lambda: FakeDatasetRepository(),
        data_health=lambda: FakeHealth(),
        risk_service=lambda: FakeRiskService(),
        risk_assessments=lambda: assessments,
        workflow_executions=lambda: executions,
        changeset_service=lambda: changesets,
        approval_service=lambda: approvals,
    )

    result = service.execute(
        current_user=CurrentUser(user_id="user-1"),
        workflow_id="workflow-1",
        inputs={},
        dataset_id="dataset-1",
    )

    assert result.status == WorkflowExecutionStatus.PENDING_APPROVAL
    assert result.changeset_id == "changeset-1"
    assert changesets.calls == [result.execution_id]
    assert executions.pending == [result.execution_id]
    assert executions.running == []
    assert engine.executed == []

    assert len(approvals.requests) == 1
    approval = approvals.requests[0]
    assert approval.execution_id == result.execution_id
    assert approval.changeset_id == "changeset-1"
    assert approval.risk_score == "HIGH"
    assert approval.confidence_score == 0.75
    assert approval.requested_by == "user-1"
    assert approval.created_at is not None
    assert approval.created_at.tzinfo is not None


def test_runtime_without_risk_metadata_remains_backward_compatible():
    from application.workflows.runtime_service import WorkflowRuntimeService
    from domain.identity import CurrentUser

    engine = FakeQueuedEngine()
    executions = FakeExecutions()
    assessments = FakeRiskAssessments()

    plan = ExecutionPlan(
        steps=(),
        metadata={},
    )

    class Engine(FakeQueuedEngine):
        def create_queued(self, **kwargs):
            kwargs["plan"] = plan
            return super().create_queued(**kwargs)

    engine = Engine()

    class LowRiskService:
        class Result:
            class Score:
                value = "LOW"

            class Confidence:
                value = 1.0

            risk_score = Score()
            confidence = Confidence()
            approval_required = False

        def evaluate(self, *, blast_radius, confidence):
            assert blast_radius == 0.0
            assert confidence == 1.0
            return self.Result()

    service = WorkflowRuntimeService(
        workflow_engine=lambda: engine,
        workflow_history=lambda: None,
        workflows=lambda: FakeWorkflowRepository(),
        workflow_queue=lambda: FakeWorkflowQueue(),
        risk_service=lambda: LowRiskService(),
        risk_assessments=lambda: assessments,
        workflow_executions=lambda: executions,
        changeset_service=lambda: changesets,
    )

    result = service.execute_async(
        current_user=CurrentUser(user_id="user-1"),
        workflow_id="workflow-1",
        inputs={},
    )

    assert result.status == WorkflowExecutionStatus.QUEUED
    assert result.changeset_id is None
    assert executions.pending == []
    assert executions.running == []
    assert assessments.created[0]["risk_score"] == "LOW"


def test_runtime_rejects_invalid_plan_blast_radius():
    from application.workflows.runtime_service import WorkflowRuntimeService
    from domain.identity import CurrentUser

    engine = FakeQueuedEngine()

    plan = ExecutionPlan(
        steps=(),
        metadata={
            "risk": {
                "blast_radius": 2.0,
            }
        },
    )

    class Engine(FakeQueuedEngine):
        def create_queued(self, **kwargs):
            kwargs["plan"] = plan
            return super().create_queued(**kwargs)

    service = WorkflowRuntimeService(
        workflow_engine=lambda: Engine(),
        workflow_history=lambda: None,
        workflows=lambda: FakeWorkflowRepository(),
        workflow_queue=lambda: FakeWorkflowQueue(),
        risk_service=lambda: FakeRiskService(),
        risk_assessments=lambda: FakeRiskAssessments(),
        workflow_executions=lambda: FakeExecutions(),
    )

    with pytest.raises(ValueError, match="blast_radius"):
        service.execute_async(
            current_user=CurrentUser(user_id="user-1"),
            workflow_id="workflow-1",
            inputs={},
        )





def test_runtime_high_risk_without_approval_service_fails_closed():
    from application.workflows.runtime_service import WorkflowRuntimeService
    from domain.identity import CurrentUser

    plan = ExecutionPlan(
        steps=(),
        metadata={
            "risk": {
                "blast_radius": 0.8,
            },
        },
    )

    class Engine(FakeQueuedEngine):
        def create_queued(self, **kwargs):
            kwargs["plan"] = plan
            return super().create_queued(**kwargs)

    engine = Engine()
    executions = FakeExecutions()
    assessments = FakeRiskAssessments()
    changesets = FakeChangeSetService()

    service = WorkflowRuntimeService(
        workflow_engine=lambda: engine,
        workflow_history=lambda: None,
        workflow_queue=lambda: FakeWorkflowQueue(),
        workflows=lambda: FakeWorkflowRepository(),
        datasets=lambda: FakeDatasetRepository(),
        data_health=lambda: FakeHealth(),
        risk_service=lambda: FakeRiskService(),
        risk_assessments=lambda: assessments,
        workflow_executions=lambda: executions,
        changeset_service=lambda: changesets,
    )

    with pytest.raises(
        RuntimeError,
        match="Approval service is required before entering PENDING_APPROVAL",
    ):
        service.execute_async(
            current_user=CurrentUser(user_id="user-1"),
            workflow_id="workflow-1",
            inputs={},
            dataset_id="dataset-1",
        )

    assert changesets.calls
    assert executions.pending == []
    assert executions.running == []
    assert engine.executed == []

class FakeWorkflowQuotaService:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def check(self, *, organization_id, dimension, requested_usage):
        self.calls.append(
            {
                "organization_id": organization_id,
                "dimension": dimension,
                "requested_usage": requested_usage,
            }
        )
        if self.error is not None:
            raise self.error


class FakeQuotaProjectRepository:
    class Project:
        workspace_id = "workspace-1"

    def get_for_owner(self, *, project_id, owner_id):
        assert project_id == "project-1"
        assert owner_id == "user-1"
        return self.Project()


class FakeQuotaWorkspaceRepository:
    class Workspace:
        organization_id = "org-1"

    def get_for_owner(self, *, workspace_id, owner_id):
        assert workspace_id == "workspace-1"
        assert owner_id == "user-1"
        return self.Workspace()


class FakeQuotaAuthorization:
    def authorize(self, **kwargs):
        return None


def test_runtime_service_checks_workflow_execution_quota():
    engine = FakeEngine()
    quota = FakeWorkflowQuotaService()

    service = WorkflowRuntimeService(
        workflow_engine=lambda: engine,
        workflow_history=FakeHistory,
        workflows=lambda: FakeWorkflowRepository(),
        projects=lambda: FakeQuotaProjectRepository(),
        workspaces=lambda: FakeQuotaWorkspaceRepository(),
        authorization=FakeQuotaAuthorization(),
        quota_service=lambda: quota,
    )

    result = service.execute(
        current_user=CurrentUser(user_id="user-1"),
        workflow_id="workflow-1",
        inputs={"source": "catalog"},
    )

    assert result == "runtime"
    assert quota.calls == [
        {
            "organization_id": "org-1",
            "dimension": QuotaDimension.WORKFLOW_EXECUTION_COUNT,
            "requested_usage": 1,
        }
    ]
    assert engine.calls


def test_runtime_service_stops_before_engine_when_workflow_quota_exceeded():
    quota = FakeWorkflowQuotaService(
        error=QuotaExceededError(
            dimension=QuotaDimension.WORKFLOW_EXECUTION_COUNT.value,
            current_usage=1,
            requested_usage=1,
            limit=1,
        )
    )

    class Engine:
        def execute(self, **kwargs):
            raise AssertionError("workflow engine must not execute")

    service = WorkflowRuntimeService(
        workflow_engine=lambda: Engine(),
        workflow_history=FakeHistory,
        workflows=lambda: FakeWorkflowRepository(),
        projects=lambda: FakeQuotaProjectRepository(),
        workspaces=lambda: FakeQuotaWorkspaceRepository(),
        authorization=FakeQuotaAuthorization(),
        quota_service=lambda: quota,
    )

    with pytest.raises(QuotaExceededError):
        service.execute(
            current_user=CurrentUser(user_id="user-1"),
            workflow_id="workflow-1",
            inputs={"source": "catalog"},
        )

    assert quota.calls == [
        {
            "organization_id": "org-1",
            "dimension": QuotaDimension.WORKFLOW_EXECUTION_COUNT,
            "requested_usage": 1,
        }
    ]

def test_runtime_service_checks_async_workflow_execution_quota():
    engine = FakeQueuedEngine()
    queue = FakeWorkflowQueue()
    quota = FakeWorkflowQuotaService()
    plan = ExecutionPlan(steps=(), metadata={})

    class Engine(FakeQueuedEngine):
        def create_queued(self, **kwargs):
            kwargs["plan"] = plan
            return super().create_queued(**kwargs)

    engine = Engine()

    service = WorkflowRuntimeService(
        workflow_engine=lambda: engine,
        workflow_history=lambda: None,
        workflows=lambda: FakeWorkflowRepository(),
        workflow_queue=lambda: queue,
        projects=lambda: FakeQuotaProjectRepository(),
        workspaces=lambda: FakeQuotaWorkspaceRepository(),
        authorization=FakeQuotaAuthorization(),
        quota_service=lambda: quota,
    )

    result = service.execute_async(
        current_user=CurrentUser(user_id="user-1"),
        workflow_id="workflow-1",
        inputs={"source": "catalog"},
    )

    assert result.execution_id in engine.executions
    assert quota.calls == [
        {
            "organization_id": "org-1",
            "dimension": QuotaDimension.WORKFLOW_EXECUTION_COUNT,
            "requested_usage": 1,
        }
    ]


def test_runtime_service_stops_before_queue_when_async_workflow_quota_exceeded():
    engine = FakeQueuedEngine()
    queue = FakeWorkflowQueue()
    quota = FakeWorkflowQuotaService(
        error=QuotaExceededError(
            dimension=QuotaDimension.WORKFLOW_EXECUTION_COUNT.value,
            current_usage=1,
            requested_usage=1,
            limit=1,
        )
    )

    service = WorkflowRuntimeService(
        workflow_engine=lambda: engine,
        workflow_history=lambda: None,
        workflows=lambda: FakeWorkflowRepository(),
        workflow_queue=lambda: queue,
        projects=lambda: FakeQuotaProjectRepository(),
        workspaces=lambda: FakeQuotaWorkspaceRepository(),
        authorization=FakeQuotaAuthorization(),
        quota_service=lambda: quota,
    )

    with pytest.raises(QuotaExceededError):
        service.execute_async(
            current_user=CurrentUser(user_id="user-1"),
            workflow_id="workflow-1",
            inputs={"source": "catalog"},
        )

    assert quota.calls == [
        {
            "organization_id": "org-1",
            "dimension": QuotaDimension.WORKFLOW_EXECUTION_COUNT,
            "requested_usage": 1,
        }
    ]
    assert engine.executions == {}
    assert queue.dispatched == []
