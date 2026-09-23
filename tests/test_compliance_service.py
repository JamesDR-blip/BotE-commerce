from unittest.mock import Mock

import pytest

from domain.compliance import CompliancePolicy
from domain.exceptions import ComplianceViolationError
from services.compliance import ComplianceService


def make_policy(
    *,
    policy_id: str = "policy-1",
    organization_id: str = "org-1",
    name: str = "policy",
    resource: str = "dataset",
    action: str = "ingest",
    condition: dict[str, str] | None = None,
    reason: str = "Policy violation",
    enabled: bool = True,
) -> CompliancePolicy:
    return CompliancePolicy(
        id=policy_id,
        organization_id=organization_id,
        name=name,
        resource=resource,
        action=action,
        condition=condition or {},
        reason=reason,
        enabled=enabled,
    )


def test_compliance_service_allows_when_no_policy_matches():
    repository = Mock()
    repository.list_for_organization.return_value = []

    service = ComplianceService(policies=repository)

    decision = service.check(
        organization_id="org-1",
        resource="dataset",
        action="ingest",
        context={"classification": "public"},
    )

    assert decision.allowed is True
    repository.list_for_organization.assert_called_once_with("org-1")


def test_compliance_service_denies_matching_policy():
    repository = Mock()
    repository.list_for_organization.return_value = [
        make_policy(
            condition={"classification": "sensitive"},
            reason="Sensitive data requires governed handling.",
        )
    ]

    service = ComplianceService(policies=repository)

    with pytest.raises(ComplianceViolationError) as exc_info:
        service.check(
            organization_id="org-1",
            resource="dataset",
            action="ingest",
            context={"classification": "sensitive"},
        )

    error = exc_info.value
    assert error.organization_id == "org-1"
    assert error.resource == "dataset"
    assert error.action == "ingest"
    assert error.reason == "Sensitive data requires governed handling."


def test_compliance_service_ignores_disabled_policy():
    repository = Mock()
    repository.list_for_organization.return_value = [
        make_policy(
            condition={},
            enabled=False,
        )
    ]

    service = ComplianceService(policies=repository)

    decision = service.check(
        organization_id="org-1",
        resource="dataset",
        action="ingest",
        context={},
    )

    assert decision.allowed is True


def test_compliance_service_ignores_different_action():
    repository = Mock()
    repository.list_for_organization.return_value = [
        make_policy(
            resource="workflow",
            action="execute",
            condition={},
        )
    ]

    service = ComplianceService(policies=repository)

    decision = service.check(
        organization_id="org-1",
        resource="dataset",
        action="ingest",
        context={},
    )

    assert decision.allowed is True


def test_compliance_service_requires_organization():
    repository = Mock()
    service = ComplianceService(policies=repository)

    with pytest.raises(ValueError, match="organization_id is required"):
        service.check(
            organization_id=None,
            resource="dataset",
            action="ingest",
            context={},
        )

    repository.list_for_organization.assert_not_called()
