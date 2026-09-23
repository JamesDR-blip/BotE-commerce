from sqlalchemy import select

from database.models import CompliancePolicyRecord
from domain.compliance import CompliancePolicy


class CompliancePolicyRepository:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    def list_for_organization(self, organization_id: str) -> list[CompliancePolicy]:
        with self._session_factory() as session:
            records = session.scalars(
                select(CompliancePolicyRecord)
                .where(
                    CompliancePolicyRecord.organization_id == organization_id,
                )
                .order_by(CompliancePolicyRecord.name)
            ).all()

            return [self._to_domain(record) for record in records]

    def get_for_organization(
        self,
        organization_id: str,
        policy_id: str,
    ) -> CompliancePolicy | None:
        with self._session_factory() as session:
            record = session.scalar(
                select(CompliancePolicyRecord).where(
                    CompliancePolicyRecord.id == policy_id,
                    CompliancePolicyRecord.organization_id == organization_id,
                )
            )
            return self._to_domain(record) if record else None

    def save(self, policy: CompliancePolicy) -> CompliancePolicy:
        with self._session_factory() as session:
            record = session.get(CompliancePolicyRecord, policy.id)

            if record is None:
                record = CompliancePolicyRecord(id=policy.id)
                session.add(record)

            elif record.organization_id != policy.organization_id:
                raise ValueError(
                    "Compliance policy organization cannot be changed"
                )

            record.organization_id = policy.organization_id
            record.name = policy.name
            record.resource = policy.resource
            record.action = policy.action
            record.condition = dict(policy.condition)
            record.reason = policy.reason
            record.enabled = policy.enabled

            session.commit()
            session.refresh(record)
            return self._to_domain(record)

    @staticmethod
    def _to_domain(record: CompliancePolicyRecord) -> CompliancePolicy:
        return CompliancePolicy(
            id=record.id,
            organization_id=record.organization_id,
            name=record.name,
            resource=record.resource,
            action=record.action,
            condition=record.condition,
            reason=record.reason,
            enabled=record.enabled,
        )
