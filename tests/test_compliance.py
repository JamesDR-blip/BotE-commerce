from domain.compliance import ComplianceDecision, CompliancePolicy


def test_compliance_policy_matches_exact_action_and_context():
    policy = CompliancePolicy(
        id="policy-1",
        organization_id="org-1",
        name="block-sensitive-ingest",
        resource="dataset",
        action="ingest",
        condition={"classification": "sensitive"},
        reason="Sensitive datasets require governed handling.",
    )

    assert policy.matches(
        resource="dataset",
        action="ingest",
        context={"classification": "sensitive"},
    )


def test_compliance_policy_does_not_match_different_context():
    policy = CompliancePolicy(
        id="policy-1",
        organization_id="org-1",
        name="block-sensitive-ingest",
        resource="dataset",
        action="ingest",
        condition={"classification": "sensitive"},
        reason="Sensitive datasets require governed handling.",
    )

    assert not policy.matches(
        resource="dataset",
        action="ingest",
        context={"classification": "public"},
    )


def test_disabled_compliance_policy_does_not_match():
    policy = CompliancePolicy(
        id="policy-1",
        organization_id="org-1",
        name="disabled-policy",
        resource="dataset",
        action="ingest",
        condition={},
        reason="Disabled.",
        enabled=False,
    )

    assert not policy.matches(
        resource="dataset",
        action="ingest",
        context={},
    )


def test_compliance_decision_allow_and_deny():
    allowed = ComplianceDecision.allow()
    denied = ComplianceDecision.deny("Policy violation")

    assert allowed.allowed is True
    assert denied.allowed is False
    assert denied.reason == "Policy violation"
