from types import SimpleNamespace

import pytest

from application.autonomous.autonomous_operations_orchestrator import (
    AutonomousOperationsOrchestrator,
)
from domain.autonomous_operations import (
    AutonomousDecision,
    AutonomousPolicy,
)
from application.autonomous.autonomous_ops_service import AutonomousOpsService


class FakeRiskService:
    def evaluate(self, *, blast_radius, confidence):
        score = "LOW" if blast_radius <= 0.1 else "HIGH"
        return SimpleNamespace(
            risk_score=SimpleNamespace(value=score),
            confidence=SimpleNamespace(value=confidence),
            approval_required=score != "LOW",
        )


class FakeSimulationService:
    def simulate(self, **kwargs):
        return SimpleNamespace(
            affected_rows=5,
            changeset_items=2,
            confidence=0.95,
        )


class FakeChangeSetMutation:
    def __init__(self, result="APPLIED"):
        self.result = result

    def apply(self, *, changeset_id, actor_id=None):
        return self.result


class FakeChangeSetRollback:
    def __init__(self, result="ROLLED_BACK"):
        self.result = result

    def rollback(self, *, changeset_id, actor_id=None):
        return self.result


class FakeChangeSets:
    def __init__(self, changeset=None):
        self.changeset = changeset

    def get(self, changeset_id):
        return self.changeset


class FakeDatasets:
    def __init__(self, dataset=None):
        self.dataset = dataset

    def get(self, dataset_id):
        return self.dataset


def make_orchestrator(
    *,
    changeset=None,
    dataset=None,
    applied="APPLIED",
    rolled_back="ROLLED_BACK",
):
    return AutonomousOperationsOrchestrator(
        data_health=SimpleNamespace(),
        requirements=SimpleNamespace(),
        planner=SimpleNamespace(),
        risk_service=FakeRiskService(),
        autonomous_ops=AutonomousOpsService(
            policy=AutonomousPolicy()
        ),
        changeset_service=SimpleNamespace(),
        changeset_mutation=FakeChangeSetMutation(applied),
        changeset_rollback=FakeChangeSetRollback(rolled_back),
        changesets=FakeChangeSets(changeset),
        datasets=FakeDatasets(dataset),
        approval_service=SimpleNamespace(),
        simulation_service=FakeSimulationService(),
    )

def test_missing_blast_radius_fails_closed():
    orchestrator = make_orchestrator()

    plan = SimpleNamespace(metadata={})

    with pytest.raises(ValueError, match="blast_radius"):
        orchestrator.govern_simulation(
            plan=plan,
            simulation_result=SimpleNamespace(
                affected_rows=1,
                changeset_items=1,
                confidence=0.9,
            ),
            health_confidence=0.9,
        )


def test_low_risk_simulation_is_auto_apply():
    orchestrator = make_orchestrator()

    plan = SimpleNamespace(
        metadata={"risk": {"blast_radius": 0.05}}
    )

    result = orchestrator.govern_simulation(
        plan=plan,
        simulation_result=SimpleNamespace(
            affected_rows=5,
            changeset_items=2,
            confidence=0.95,
        ),
        health_confidence=0.9,
    )

    assert result.decision == AutonomousDecision.AUTO_APPLY
    assert result.risk_score == "LOW"


def test_high_risk_simulation_requires_approval():
    orchestrator = make_orchestrator()

    plan = SimpleNamespace(
        metadata={"risk": {"blast_radius": 0.5}}
    )

    result = orchestrator.govern_simulation(
        plan=plan,
        simulation_result=SimpleNamespace(
            affected_rows=5,
            changeset_items=2,
            confidence=0.95,
        ),
        health_confidence=0.9,
    )

    assert result.decision == AutonomousDecision.REQUIRE_APPROVAL
    assert result.risk_score == "HIGH"


def test_affected_rows_guardrail_blocks():
    orchestrator = make_orchestrator()

    plan = SimpleNamespace(
        metadata={"risk": {"blast_radius": 0.05}}
    )

    result = orchestrator.govern_simulation(
        plan=plan,
        simulation_result=SimpleNamespace(
            affected_rows=101,
            changeset_items=2,
            confidence=0.95,
        ),
        health_confidence=0.9,
    )

    assert result.decision == AutonomousDecision.BLOCKED


def test_changeset_items_guardrail_blocks():
    orchestrator = make_orchestrator()

    plan = SimpleNamespace(
        metadata={"risk": {"blast_radius": 0.05}}
    )

    result = orchestrator.govern_simulation(
        plan=plan,
        simulation_result=SimpleNamespace(
            affected_rows=5,
            changeset_items=101,
            confidence=0.95,
        ),
        health_confidence=0.9,
    )

    assert result.decision == AutonomousDecision.BLOCKED


def test_simulation_uses_owner_as_current_user():
    orchestrator = make_orchestrator()

    result = orchestrator.simulate(
        workflow_id="workflow-1",
        owner_id="owner-1",
        inputs={"x": 1},
        dataset_id="dataset-1",
    )

    assert result.affected_rows == 5


def test_verify_candidate_succeeds_when_dataset_matches_changeset():
    changeset = SimpleNamespace(
        dataset_id="dataset-1",
        after_storage_key="storage-after",
        after_content_hash="hash-after",
    )
    dataset = SimpleNamespace(
        storage_key="storage-after",
        content_hash="hash-after",
    )

    orchestrator = make_orchestrator(
        changeset=changeset,
        dataset=dataset,
    )

    result = orchestrator.verify_candidate(
        changeset_id="changeset-1",
        dataset_id="dataset-1",
    )

    assert result["verified"] is True
    assert result["storage_key_match"] is True
    assert result["content_hash_match"] is True


def test_verify_candidate_fails_when_dataset_pointer_does_not_match():
    changeset = SimpleNamespace(
        dataset_id="dataset-1",
        after_storage_key="storage-after",
        after_content_hash="hash-after",
    )
    dataset = SimpleNamespace(
        storage_key="unexpected-storage",
        content_hash="hash-after",
    )

    orchestrator = make_orchestrator(
        changeset=changeset,
        dataset=dataset,
    )

    result = orchestrator.verify_candidate(
        changeset_id="changeset-1",
        dataset_id="dataset-1",
    )

    assert result["verified"] is False
    assert result["storage_key_match"] is False
    assert result["content_hash_match"] is True


def test_auto_apply_verifies_successfully():
    changeset = SimpleNamespace(
        dataset_id="dataset-1",
        after_storage_key="storage-after",
        after_content_hash="hash-after",
    )
    dataset = SimpleNamespace(
        storage_key="storage-after",
        content_hash="hash-after",
    )

    orchestrator = make_orchestrator(
        changeset=changeset,
        dataset=dataset,
        applied="APPLIED",
    )

    evaluation = SimpleNamespace(
        decision=AutonomousDecision.AUTO_APPLY,
        reason="safe",
        risk_score="LOW",
        confidence=0.95,
    )

    result = orchestrator.decide_and_route(
        evaluation=evaluation,
        execution_id="execution-1",
        changeset_id="changeset-1",
        requested_by="user-1",
    )

    assert result["decision"] == "AUTO_APPLY"
    assert result["applied"] == "APPLIED"
    assert result["verified"] is True
    assert result["verification"]["verified"] is True


def test_auto_apply_rolls_back_when_verification_fails():
    changeset = SimpleNamespace(
        dataset_id="dataset-1",
        after_storage_key="storage-after",
        after_content_hash="hash-after",
    )
    dataset = SimpleNamespace(
        storage_key="unexpected-storage",
        content_hash="hash-after",
    )

    orchestrator = make_orchestrator(
        changeset=changeset,
        dataset=dataset,
        applied="APPLIED",
        rolled_back="ROLLED_BACK",
    )

    evaluation = SimpleNamespace(
        decision=AutonomousDecision.AUTO_APPLY,
        reason="safe",
        risk_score="LOW",
        confidence=0.95,
    )

    result = orchestrator.decide_and_route(
        evaluation=evaluation,
        execution_id="execution-1",
        changeset_id="changeset-1",
        requested_by="user-1",
    )

    assert result["decision"] == "AUTO_APPLY"
    assert result["verified"] is False
    assert result["rolled_back"] == "ROLLED_BACK"
    assert result["verification"]["verified"] is False




class FakeWorkflowAuthoringForRun:
    def __init__(self):
        self.calls = []

    def save_workflow(self, **kwargs):
        self.calls.append(kwargs)
        return type(
            "Workflow",
            (),
            {
                "id": kwargs["workflow_id"],
                "active_version": kwargs["version"],
                "status": "DRAFT",
            },
        )()


class FakeWorkflowExecutionsForRun:
    def __init__(self):
        self.created = []
        self.pending = []
        self.completed = []
        self.failed = []

    def create(self, **kwargs):
        self.created.append(kwargs)
        return type("Execution", (), kwargs)()

    def mark_pending_approval(self, execution_id):
        self.pending.append(execution_id)

    def complete(self, *, execution_id, outputs_json):
        self.completed.append(
            {
                "execution_id": execution_id,
                "outputs_json": outputs_json,
            }
        )

    def fail(self, *, execution_id, error):
        self.failed.append(
            {
                "execution_id": execution_id,
                "error": error,
            }
        )


class FakeHealthForRun:
    overall_score = 100.0


class FakeChangeSetForRun:
    def __init__(self, changeset_id="changeset-run-1"):
        self.id = changeset_id
        self.status = "PREPARED"
        self.dataset_id = "dataset-1"


class FakeChangeSetsForRun:
    def __init__(self, changeset):
        self.changeset = changeset

    def get(self, changeset_id):
        return self.changeset if changeset_id == self.changeset.id else None


class FakeDataSetsForRun:
    def __init__(self):
        self.values = {}

    def get(self, dataset_id):
        return self.values.get(dataset_id)


class FakeSimulationForRun:
    def __init__(self, *, affected_rows=1, changeset_items=1, confidence=0.99):
        self.affected_rows = affected_rows
        self.changeset_items = changeset_items
        self.confidence = confidence


def _make_run_orchestrator(
    *,
    evaluation,
    simulation=None,
    verified=True,
):
    from application.autonomous.autonomous_operations_orchestrator import (
        AutonomousOperationsOrchestrator,
    )

    changeset = FakeChangeSetForRun()
    workflow_authoring = FakeWorkflowAuthoringForRun()
    workflow_executions = FakeWorkflowExecutionsForRun()

    class FakeDataHealth:
        def get_health(self, **kwargs):
            return FakeHealthForRun()

        def get_diagnostics(self, **kwargs):
            return {"status": "healthy", "issues": []}

        def get_remediation_proposals(self, **kwargs):
            return []

    class FakeRequirements:
        def interpret(self, **kwargs):
            return type("Requirement", (), {})()

    class FakePlanner:
        def plan(self, requirement):
            return type(
                "Plan",
                (),
                {
                    "metadata": {
                        "risk": {
                            "blast_radius": 0.05,
                        }
                    }
                },
            )()

    class FakeRisk:
        def evaluate(self, blast_radius, confidence):
            return type(
                "Risk",
                (),
                {
                    "risk_score": type("RiskScore", (), {"value": "LOW"})(),
                    "confidence": type("ConfidenceScore", (), {"value": 0.99})(),
                    "approval_required": False,
                },
            )()

    class FakeAutonomousOps:
        def evaluate(self, **kwargs):
            return evaluation

    class FakeChangeSetService:
        def prepare_candidate(self, *, execution_id):
            return changeset

    class FakeMutation:
        def __init__(self):
            self.calls = []

        def apply(self, **kwargs):
            self.calls.append(kwargs)
            return changeset

    class FakeRollback:
        def __init__(self):
            self.calls = []

        def rollback(self, **kwargs):
            self.calls.append(kwargs)
            return changeset

    class FakeApproval:
        def __init__(self):
            self.calls = []

        def request_approval(self, request):
            self.calls.append(request)
            return "approval-token"

    class FakeSimulationService:
        def simulate(self, **kwargs):
            return simulation or FakeSimulationForRun()

    class FakeMemory:
        def __init__(self):
            self.calls = []

        def record_learning(self, learning):
            self.calls.append(learning)

    orchestrator = AutonomousOperationsOrchestrator(
        data_health=FakeDataHealth(),
        requirements=FakeRequirements(),
        planner=FakePlanner(),
        risk_service=FakeRisk(),
        autonomous_ops=FakeAutonomousOps(),
        changeset_service=FakeChangeSetService(),
        changeset_mutation=FakeMutation(),
        changeset_rollback=FakeRollback(),
        changesets=FakeChangeSetsForRun(changeset),
        datasets=FakeDataSetsForRun(),
        approval_service=FakeApproval(),
        workflow_authoring=workflow_authoring,
        workflow_executions=workflow_executions,
        simulation_service=FakeSimulationService(),
        memory_service=FakeMemory(),
        audit_service=None,
    )

    orchestrator._test_mutation = orchestrator._changeset_mutation
    orchestrator._test_rollback = orchestrator._changeset_rollback
    orchestrator._test_memory = orchestrator._memory_service
    orchestrator._test_workflow_executions = workflow_executions

    original_verify = orchestrator.verify_candidate

    def verify_candidate_for_test(*, changeset_id, dataset_id):
        return {"verified": verified}

    orchestrator.verify_candidate = verify_candidate_for_test

    return orchestrator


def test_run_low_risk_closed_loop():
    from domain.autonomous_operations import (
        AutonomousDecision,
        AutonomousEvaluation,
    )

    evaluation = AutonomousEvaluation(
        decision=AutonomousDecision.AUTO_APPLY,
        reason="low-risk autonomous remediation",
        risk_score="LOW",
        confidence=0.99,
    )

    orchestrator = _make_run_orchestrator(evaluation=evaluation)

    result = orchestrator.run(
        user_id="user-1",
        workspace_id="workspace-1",
        request="low-risk defect remediation",
        workflow_id="wf-run-1",
        workflow_name="Autonomous remediation",
        workflow_version="1.0",
        project_id="project-1",
        inputs={"issue": "low-risk defect"},
        dataset_id="dataset-1",
    )

    assert result["evaluation"].decision is AutonomousDecision.AUTO_APPLY
    assert result["route"]["status"] == "APPLIED"
    assert result["verified"] is True

    executions = orchestrator._test_workflow_executions
    assert len(executions.created) == 1
    assert len(executions.completed) == 1
    assert executions.failed == []


def test_run_high_risk_waits_for_approval():
    from domain.autonomous_operations import (
        AutonomousDecision,
        AutonomousEvaluation,
    )

    evaluation = AutonomousEvaluation(
        decision=AutonomousDecision.REQUIRE_APPROVAL,
        reason="high-risk action requires approval",
        risk_score="HIGH",
        confidence=0.99,
    )

    orchestrator = _make_run_orchestrator(evaluation=evaluation)

    result = orchestrator.run(
        user_id="user-1",
        workspace_id="workspace-1",
        request="high-risk defect remediation",
        workflow_id="wf-run-2",
        workflow_name="High-risk remediation",
        workflow_version="1.0",
        project_id="project-1",
        inputs={"issue": "high-risk defect"},
        dataset_id="dataset-1",
    )

    assert result["evaluation"].decision is AutonomousDecision.REQUIRE_APPROVAL
    assert result["route"]["status"] == "PENDING_APPROVAL"

    executions = orchestrator._test_workflow_executions
    assert len(executions.pending) == 1
    assert executions.completed == []
    assert executions.failed == []


def test_run_blocked_guardrail_does_not_apply():
    from domain.autonomous_operations import (
        AutonomousDecision,
        AutonomousEvaluation,
    )

    evaluation = AutonomousEvaluation(
        decision=AutonomousDecision.BLOCKED,
        reason="blast radius exceeds autonomous ceiling",
        risk_score="LOW",
        confidence=0.99,
    )

    orchestrator = _make_run_orchestrator(evaluation=evaluation)

    result = orchestrator.run(
        user_id="user-1",
        workspace_id="workspace-1",
        request="unsafe defect remediation",
        workflow_id="wf-run-3",
        workflow_name="Blocked remediation",
        workflow_version="1.0",
        project_id="project-1",
        inputs={"issue": "unsafe defect"},
        dataset_id="dataset-1",
    )

    assert result["evaluation"].decision is AutonomousDecision.BLOCKED
    assert result["route"]["status"] == "BLOCKED"

    executions = orchestrator._test_workflow_executions
    assert executions.pending == []
    assert executions.completed == []
    assert len(executions.failed) == 1
    assert executions.failed[0]["execution_id"] == result["execution_id"]
    assert "Autonomous operation blocked:" in executions.failed[0]["error"]


def test_run_verification_failure_marks_execution_failed():
    from domain.autonomous_operations import (
        AutonomousDecision,
        AutonomousEvaluation,
    )

    evaluation = AutonomousEvaluation(
        decision=AutonomousDecision.AUTO_APPLY,
        reason="low-risk autonomous remediation",
        risk_score="LOW",
        confidence=0.99,
    )

    orchestrator = _make_run_orchestrator(
        evaluation=evaluation,
        verified=False,
    )

    result = orchestrator.run(
        user_id="user-1",
        workspace_id="workspace-1",
        request="defect remediation",
        workflow_id="wf-run-4",
        workflow_name="Verification failure",
        workflow_version="1.0",
        project_id="project-1",
        inputs={"issue": "defect"},
        dataset_id="dataset-1",
    )

    assert result["evaluation"].decision is AutonomousDecision.AUTO_APPLY
    assert result["verified"] is False

    executions = orchestrator._test_workflow_executions
    assert executions.completed == []
    assert len(executions.failed) == 1

