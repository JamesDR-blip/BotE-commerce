from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, CompliancePolicyRecord, OrganizationRecord
from domain.compliance import CompliancePolicy
from repositories.compliance_policies import CompliancePolicyRepository


def test_compliance_policy_repository_persists_and_isolates_tenants(tmp_path):
    db_path = tmp_path / "compliance.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    org_a = str(uuid4())
    org_b = str(uuid4())

    with SessionLocal() as session:
        session.add_all(
            [
                OrganizationRecord(
                    id=org_a,
                    name="Organization A",
                ),
                OrganizationRecord(
                    id=org_b,
                    name="Organization B",
                ),
            ]
        )
        session.commit()

    repository = CompliancePolicyRepository(SessionLocal)

    policy_a = CompliancePolicy(
        id=str(uuid4()),
        organization_id=org_a,
        name="sensitive-ingest",
        resource="dataset",
        action="ingest",
        condition={"classification": "sensitive"},
        reason="Sensitive data requires additional governance.",
    )

    policy_b = CompliancePolicy(
        id=str(uuid4()),
        organization_id=org_b,
        name="other-policy",
        resource="workflow",
        action="execute",
        condition={"environment": "production"},
        reason="Production workflow execution is governed.",
    )

    repository.save(policy_a)
    repository.save(policy_b)

    loaded = repository.get_for_organization(org_a, policy_a.id)
    assert loaded == policy_a

    assert repository.get_for_organization(org_b, policy_a.id) is None

    policies_a = repository.list_for_organization(org_a)
    policies_b = repository.list_for_organization(org_b)

    assert [policy.id for policy in policies_a] == [policy_a.id]
    assert [policy.id for policy in policies_b] == [policy_b.id]


def test_compliance_policy_repository_updates_same_tenant(tmp_path):
    db_path = tmp_path / "compliance-update.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    organization_id = str(uuid4())

    with SessionLocal() as session:
        session.add(
            OrganizationRecord(
                id=organization_id,
                name="Organization",
            )
        )
        session.commit()

    repository = CompliancePolicyRepository(SessionLocal)

    policy_id = str(uuid4())

    repository.save(
        CompliancePolicy(
            id=policy_id,
            organization_id=organization_id,
            name="policy",
            resource="dataset",
            action="ingest",
            condition={"classification": "sensitive"},
            reason="Initial reason",
        )
    )

    updated = CompliancePolicy(
        id=policy_id,
        organization_id=organization_id,
        name="policy",
        resource="dataset",
        action="ingest",
        condition={"classification": "restricted"},
        reason="Updated reason",
        enabled=False,
    )

    repository.save(updated)

    assert repository.get_for_organization(
        organization_id,
        policy_id,
    ) == updated
