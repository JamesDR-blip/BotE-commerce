from domain.autonomous_operations import AutonomousDecision, AutonomousPolicy
from application.autonomous.autonomous_ops_service import AutonomousOpsService


def make_service() -> AutonomousOpsService:
    return AutonomousOpsService(policy=AutonomousPolicy())



def test_low_risk_operation_is_auto_applied() -> None:
    service = make_service()
    result = service.evaluate(
        risk_score="LOW",
        blast_radius=0.05,
        affected_rows=10,
        changeset_items=10,
    )
    assert result.decision is AutonomousDecision.AUTO_APPLY

def test_high_risk_operation_requires_approval() -> None:
    service = make_service()
    result = service.evaluate(
        risk_score="HIGH",
        blast_radius=0.05,
        affected_rows=10,
        changeset_items=10,
    )
    assert result.decision is AutonomousDecision.REQUIRE_APPROVAL

def test_critical_risk_operation_requires_approval() -> None:
    service = make_service()
    result = service.evaluate(
        risk_score="CRITICAL",
        blast_radius=0.05,
        affected_rows=10,
        changeset_items=10,
    )
    assert result.decision is AutonomousDecision.REQUIRE_APPROVAL

def test_medium_risk_operation_is_blocked() -> None:
    service = make_service()
    result = service.evaluate(
        risk_score="MEDIUM",
        blast_radius=0.05,
        affected_rows=10,
        changeset_items=10,
    )
    assert result.decision is AutonomousDecision.BLOCKED

def test_blast_radius_limit_blocks_operation() -> None:
    result = make_service().evaluate(
        risk_score="LOW", blast_radius=0.11, affected_rows=10, changeset_items=10
    )
    assert result.decision is AutonomousDecision.BLOCKED

def test_affected_rows_limit_blocks_operation() -> None:
    result = make_service().evaluate(
        risk_score="LOW", blast_radius=0.05, affected_rows=101, changeset_items=10
    )
    assert result.decision is AutonomousDecision.BLOCKED

def test_changeset_items_limit_blocks_operation() -> None:
    result = make_service().evaluate(
        risk_score="LOW", blast_radius=0.05, affected_rows=10, changeset_items=101
    )
    assert result.decision is AutonomousDecision.BLOCKED

def test_operation_limit_blocks_operation() -> None:
    result = make_service().evaluate(
        risk_score="LOW", blast_radius=0.05, affected_rows=10, changeset_items=10, operations=2
    )
    assert result.decision is AutonomousDecision.BLOCKED

def test_iteration_limit_blocks_operation() -> None:
    result = make_service().evaluate(
        risk_score="LOW", blast_radius=0.05, affected_rows=10, changeset_items=10, iterations=2
    )
    assert result.decision is AutonomousDecision.BLOCKED

def test_consecutive_failure_limit_blocks_operation() -> None:
    result = make_service().evaluate(
        risk_score="LOW", blast_radius=0.05, affected_rows=10, changeset_items=10, consecutive_failures=2
    )
    assert result.decision is AutonomousDecision.BLOCKED

def test_high_risk_is_routed_to_approval_even_above_autonomous_blast_radius():
    service = AutonomousOpsService(
        policy=AutonomousPolicy(max_blast_radius=0.1)
    )

    result = service.evaluate(
        risk_score="HIGH",
        blast_radius=0.5,
        affected_rows=5,
        changeset_items=2,
    )

    assert result.decision == AutonomousDecision.REQUIRE_APPROVAL


def test_low_risk_above_autonomous_blast_radius_is_blocked():
    service = AutonomousOpsService(
        policy=AutonomousPolicy(max_blast_radius=0.1)
    )

    result = service.evaluate(
        risk_score="LOW",
        blast_radius=0.2,
        affected_rows=5,
        changeset_items=2,
    )

    assert result.decision == AutonomousDecision.BLOCKED
