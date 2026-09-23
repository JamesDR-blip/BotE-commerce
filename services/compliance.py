from __future__ import annotations

from collections.abc import Mapping

from domain.compliance import ComplianceDecision
from domain.exceptions import ComplianceViolationError
from repositories.compliance_policies import CompliancePolicyRepository


class ComplianceService:
    """Deterministic organization-scoped compliance policy enforcement."""

    def __init__(
        self,
        *,
        policies: CompliancePolicyRepository,
    ) -> None:
        self.policies = policies

    def check(
        self,
        *,
        organization_id: str | None,
        resource: str,
        action: str,
        context: Mapping[str, str],
    ) -> ComplianceDecision:
        if organization_id is None or not organization_id.strip():
            raise ValueError(
                "organization_id is required for compliance evaluation"
            )

        if not resource or not resource.strip():
            raise ValueError("resource must not be blank")

        if not action or not action.strip():
            raise ValueError("action must not be blank")

        for policy in self.policies.list_for_organization(organization_id):
            if policy.matches(
                resource=resource,
                action=action,
                context=context,
            ):
                raise ComplianceViolationError(
                    organization_id=organization_id,
                    resource=resource,
                    action=action,
                    reason=policy.reason,
                )

        return ComplianceDecision.allow()
