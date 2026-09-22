from datetime import datetime, timedelta, timezone
import hashlib

import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_approval_service, get_current_user
from api.main import create_app
from application.approval.approval_service import ApprovalService
from application.risk.risk_service import RiskService
from configs.settings import Settings
from repositories.rbac import RBACRepository
from services.authorization import AuthorizationService
from domain.approval import ApprovalDecision, ApprovalRequest
from domain.identity import CurrentUser
from domain.risk import RiskPolicy, RiskScore


VALID_TOKEN = "test-approval-token"
VALID_TOKEN_HASH = hashlib.sha256(VALID_TOKEN.encode("utf-8")).hexdigest()


class FakeApprovalRecord:
    def __init__(
        self,
        approval_id="approval-1",
        execution_id="execution-1",
        changeset_id="changeset-1",
        decision=None,
        expires_at=None,
        token_hash=VALID_TOKEN_HASH,
    ):
        self.approval_id = approval_id
        self.execution_id = execution_id
        self.changeset_id = changeset_id
        self.risk_score = "HIGH"
        self.confidence_score = 0.85
        self.requested_by = "requester"
        self.created_at = datetime.now(timezone.utc)
        self.expires_at = expires_at
        self.decision = decision
        self.token_hash = token_hash


class FakeApprovalRepository:
    def __init__(self, record=None):
        self.record = record
        self.updated = []
        self.created_token_hash = None

    def create(self, request, *, token_hash):
        self.created_token_hash = token_hash
        self.record = FakeApprovalRecord(
            approval_id=request.approval_id,
            execution_id=request.execution_id,
            changeset_id=request.changeset_id,
            expires_at=request.expires_at,
            token_hash=token_hash,
        )
        return self.record

    def get(self, approval_id):
        if self.record is None or self.record.approval_id != approval_id:
            return None
        return self.record

    def update_decision(self, approval_id, decision):
        if self.record is None or self.record.approval_id != approval_id:
            raise ValueError(f"Approval {approval_id} not found")
        self.record.decision = decision.value
        self.updated.append((approval_id, decision))


class FakeWorkflowExecutions:
    def __init__(self):
        self.released = []
        self.cancelled = []

    def release_to_queue(self, execution_id):
        self.released.append(execution_id)

    def cancel(self, execution_id):
        self.cancelled.append(execution_id)


class FakeWorkflowQueue:
    def __init__(self):
        self.dispatched = []

    def dispatch(self, execution_id):
        self.dispatched.append(execution_id)


class FakeApprovalChangeSetService:
    def __init__(self):
        self.applied = []

    def apply(self, *, approval_id):
        self.applied.append(approval_id)


def approver():
    return CurrentUser(
        user_id="approver",
        roles=frozenset({"approver"}),
    )


def ordinary_user():
    return CurrentUser(
        user_id="user",
        roles=frozenset({"user"}),
    )


def test_risk_policy_classifies_scores():
    policy = RiskPolicy()

    assert policy.classify(0.1) == RiskScore.LOW
    assert policy.classify(0.4) == RiskScore.MEDIUM
    assert policy.classify(0.7) == RiskScore.HIGH
    assert policy.classify(0.9) == RiskScore.CRITICAL


def test_risk_service_requires_approval_for_high_risk():
    service = RiskService()

    result = service.evaluate(
        blast_radius=0.8,
        confidence=0.85,
    )

    assert result.risk_score == RiskScore.HIGH
    assert result.confidence.value == 0.85
    assert result.approval_required is True


def test_risk_service_does_not_require_approval_for_low_risk():
    service = RiskService()

    result = service.evaluate(
        blast_radius=0.1,
        confidence=0.95,
    )

    assert result.risk_score == RiskScore.LOW
    assert result.approval_required is False


def test_risk_service_rejects_invalid_confidence():
    service = RiskService()

    with pytest.raises(ValueError, match="confidence"):
        service.evaluate(
            blast_radius=0.5,
            confidence=1.1,
        )


def test_approval_service_get_for_execution_returns_pending_approval():
    first = FakeApprovalRecord()
    first.approval_id = "approval-1"
    first.execution_id = "execution-1"
    first.decision = "APPROVED"

    second = FakeApprovalRecord()
    second.approval_id = "approval-2"
    second.execution_id = "execution-1"
    second.decision = None

    class Repository(FakeApprovalRepository):
        def __init__(self):
            super().__init__()
            self.records = [second, first]

        def get_by_execution_id(self, execution_id):
            return [
                record
                for record in self.records
                if record.execution_id == execution_id
            ]

    service = ApprovalService(Repository())

    approval = service.get_for_execution("execution-1")

    assert approval is second


def test_approval_service_get_for_execution_returns_none_without_pending():
    record = FakeApprovalRecord()
    record.execution_id = "execution-1"
    record.decision = "REJECTED"

    class Repository(FakeApprovalRepository):
        def get_by_execution_id(self, execution_id):
            if execution_id == record.execution_id:
                return [record]
            return []

    service = ApprovalService(Repository())

    assert service.get_for_execution("execution-1") is None

def test_approval_service_list_pending_enforces_rbac_organization_scope():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.models import Base

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    rbac = RBACRepository(sessions)

    rbac.create_role(
        role_id="role-reviewer",
        name="reviewer",
    )
    rbac.create_permission(
        permission_id="permission-approval-read",
        resource="approval",
        action="read",
    )
    rbac.assign_permission_to_role(
        role_id="role-reviewer",
        permission_id="permission-approval-read",
    )
    rbac.create_membership(
        membership_id="membership-org-1",
        user_id="user-1",
        organization_id="org-1",
        role_id="role-reviewer",
    )
    rbac.create_role(
        role_id="role-viewer",
        name="viewer",
    )
    rbac.create_membership(
        membership_id="membership-org-2",
        user_id="user-1",
        organization_id="org-2",
        role_id="role-viewer",
    )

    class Repository:
        def __init__(self):
            self.organizations = []

        def list_pending_for_organization(self, *, organization_id):
            self.organizations.append(organization_id)
            return [f"approval-{organization_id}"]

        def list_pending(self):
            raise AssertionError("unscoped list_pending must not be called")

    repository = Repository()
    service = ApprovalService(
        repository,
        authorization=AuthorizationService(rbac),
    )

    approvals = service.list_pending(user=CurrentUser(user_id="user-1"))

    assert approvals == ["approval-org-1"]
    assert repository.organizations == ["org-1"]

def test_approval_request_generates_and_persists_only_token_hash():
    repository = FakeApprovalRepository()
    service = ApprovalService(repository)

    request = ApprovalRequest(
        approval_id="approval-1",
        execution_id="execution-1",
        changeset_id="changeset-1",
        risk_score="HIGH",
        confidence_score=0.85,
        requested_by="requester",
        created_at=datetime.now(timezone.utc),
    )

    token = service.request_approval(request)

    assert token
    assert token != repository.created_token_hash
    assert len(repository.created_token_hash) == 64
    assert repository.created_token_hash == hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def test_approval_approved_applies_changeset_without_requeue():
    repository = FakeApprovalRepository(
        FakeApprovalRecord()
    )
    executions = FakeWorkflowExecutions()
    queue = FakeWorkflowQueue()
    changesets = FakeApprovalChangeSetService()

    service = ApprovalService(
        repository,
        workflow_executions=executions,
        workflow_queue=queue,
        approval_changeset_service=changesets,
    )

    service.decide(
        "approval-1",
        ApprovalDecision.APPROVED,
        user=approver(),
        token=VALID_TOKEN,
    )

    assert changesets.applied == ["approval-1"]
    assert executions.released == []
    assert executions.cancelled == []
    assert queue.dispatched == []

def test_approval_rejected_cancels_without_dispatch():
    repository = FakeApprovalRepository(
        FakeApprovalRecord()
    )
    executions = FakeWorkflowExecutions()
    queue = FakeWorkflowQueue()

    service = ApprovalService(
        repository,
        workflow_executions=executions,
        workflow_queue=queue,
    )

    service.decide(
        "approval-1",
        ApprovalDecision.REJECTED,
        user=approver(),
        token=VALID_TOKEN,
    )

    assert executions.released == []
    assert executions.cancelled == ["execution-1"]
    assert queue.dispatched == []
    assert repository.updated == [
        ("approval-1", ApprovalDecision.REJECTED)
    ]


def test_expired_approval_cannot_be_approved():
    repository = FakeApprovalRepository(
        FakeApprovalRecord(
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)
        )
    )
    executions = FakeWorkflowExecutions()
    queue = FakeWorkflowQueue()

    service = ApprovalService(
        repository,
        workflow_executions=executions,
        workflow_queue=queue,
    )

    with pytest.raises(ValueError, match="expired"):
        service.decide(
            "approval-1",
            ApprovalDecision.APPROVED,
            user=approver(),
            token=VALID_TOKEN,
        )

    assert executions.released == []
    assert executions.cancelled == []
    assert queue.dispatched == []
    assert repository.record.decision == ApprovalDecision.EXPIRED.value


def test_already_decided_approval_cannot_be_decided_again():
    repository = FakeApprovalRepository(
        FakeApprovalRecord(
            decision=ApprovalDecision.APPROVED.value
        )
    )
    executions = FakeWorkflowExecutions()
    queue = FakeWorkflowQueue()

    service = ApprovalService(
        repository,
        workflow_executions=executions,
        workflow_queue=queue,
    )

    with pytest.raises(ValueError, match="already been decided"):
        service.decide(
            "approval-1",
            ApprovalDecision.REJECTED,
            user=approver(),
            token=VALID_TOKEN,
        )

    assert executions.released == []
    assert executions.cancelled == []
    assert queue.dispatched == []


def test_non_approver_cannot_decide():
    repository = FakeApprovalRepository(
        FakeApprovalRecord()
    )
    executions = FakeWorkflowExecutions()
    queue = FakeWorkflowQueue()

    service = ApprovalService(
        repository,
        workflow_executions=executions,
        workflow_queue=queue,
    )

    with pytest.raises(PermissionError, match="Approver role"):
        service.decide(
            "approval-1",
            ApprovalDecision.APPROVED,
            user=ordinary_user(),
            token=VALID_TOKEN,
        )

    assert repository.updated == []
    assert executions.released == []
    assert executions.cancelled == []
    assert queue.dispatched == []


def test_invalid_approval_token_is_rejected():
    repository = FakeApprovalRepository(
        FakeApprovalRecord()
    )
    executions = FakeWorkflowExecutions()
    queue = FakeWorkflowQueue()

    service = ApprovalService(
        repository,
        workflow_executions=executions,
        workflow_queue=queue,
    )

    with pytest.raises(ValueError, match="Invalid approval token"):
        service.decide(
            "approval-1",
            ApprovalDecision.APPROVED,
            user=approver(),
            token="wrong-token",
        )

    assert repository.updated == []
    assert executions.released == []
    assert executions.cancelled == []
    assert queue.dispatched == []


def test_missing_approval_token_is_rejected():
    repository = FakeApprovalRepository(
        FakeApprovalRecord()
    )
    service = ApprovalService(repository)

    with pytest.raises(ValueError, match="Approval token is required"):
        service.decide(
            "approval-1",
            ApprovalDecision.APPROVED,
            user=approver(),
            token="",
        )


def test_approval_with_missing_persisted_token_hash_is_rejected():
    repository = FakeApprovalRepository(
        FakeApprovalRecord(token_hash=None)
    )
    service = ApprovalService(repository)

    with pytest.raises(ValueError, match="token"):
        service.decide(
            "approval-1",
            ApprovalDecision.APPROVED,
            user=approver(),
            token=VALID_TOKEN,
        )


@pytest.mark.parametrize(
    "method,path",
    [
        ("post", "/approval/decision"),
        ("post", "/approvals/approval-1/approve"),
        ("post", "/approvals/approval-1/reject"),
    ],
)
def test_approval_mutations_require_authentication(method, path):
    app = create_app(Settings(database_url="sqlite://"))
    client = TestClient(app)

    kwargs = {}

    if path == "/approval/decision":
        kwargs["json"] = {
            "approval_id": "approval-1",
            "decision": "APPROVED",
            "token": VALID_TOKEN,
        }
    else:
        kwargs["json"] = {"token": VALID_TOKEN}

    response = getattr(client, method)(path, **kwargs)

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_approval_request_uses_authenticated_user_as_requester():
    app = create_app(Settings(database_url="sqlite://"))
    captured = {}

    class FakeApprovalService:
        def request_approval(self, request):
            captured["request"] = request
            return "one-time-token"

    app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="authenticated-user")
    )
    app.dependency_overrides[get_approval_service] = (
        lambda: FakeApprovalService()
    )

    client = TestClient(app)

    response = client.post(
        "/approval/request",
        json={
            "approval_id": "approval-1",
            "execution_id": "execution-1",
            "changeset_id": "changeset-1",
            "risk_score": "HIGH",
            "confidence_score": 0.85,
            "requested_by": "attacker-supplied-user",
        },
    )

    assert response.status_code == 201
    assert response.json()["token"] == "one-time-token"
    assert captured["request"].requested_by == "authenticated-user"


def test_pending_approval_response_does_not_expose_token_or_hash():
    app = create_app(Settings(database_url="sqlite://"))

    class FakeApprovalService:
        def list_pending(self, *, user):
            assert user == CurrentUser(user_id="authenticated-user")
            return [
                FakeApprovalRecord()
            ]

    app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="authenticated-user")
    )
    app.dependency_overrides[get_approval_service] = (
        lambda: FakeApprovalService()
    )

    client = TestClient(app)

    response = client.get("/approvals/pending")

    assert response.status_code == 200
    body = response.json()

    assert len(body) == 1
    assert "token" not in body[0]
    assert "token_hash" not in body[0]

def test_approve_endpoint_accepts_token_in_json_body():
    app = create_app(Settings(database_url="sqlite://"))
    captured = {}

    class FakeApprovalService:
        def decide(self, approval_id, decision, *, user, token):
            captured.update(
                approval_id=approval_id,
                decision=decision,
                user=user,
                token=token,
            )

    app.dependency_overrides[get_current_user] = (
        lambda: approver()
    )
    app.dependency_overrides[get_approval_service] = (
        lambda: FakeApprovalService()
    )

    client = TestClient(app)

    response = client.post(
        "/approvals/approval-1/approve",
        json={"token": VALID_TOKEN},
    )

    assert response.status_code == 200
    assert captured["approval_id"] == "approval-1"
    assert captured["decision"] == ApprovalDecision.APPROVED
    assert captured["token"] == VALID_TOKEN


def test_reject_endpoint_accepts_token_in_json_body():
    app = create_app(Settings(database_url="sqlite://"))
    captured = {}

    class FakeApprovalService:
        def decide(self, approval_id, decision, *, user, token):
            captured.update(
                approval_id=approval_id,
                decision=decision,
                user=user,
                token=token,
            )

    app.dependency_overrides[get_current_user] = (
        lambda: approver()
    )
    app.dependency_overrides[get_approval_service] = (
        lambda: FakeApprovalService()
    )

    client = TestClient(app)

    response = client.post(
        "/approvals/approval-1/reject",
        json={"token": VALID_TOKEN},
    )

    assert response.status_code == 200
    assert captured["approval_id"] == "approval-1"
    assert captured["decision"] == ApprovalDecision.REJECTED
    assert captured["token"] == VALID_TOKEN







