from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from repositories.organizations import OrganizationRepository


def create_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


def test_create_and_get_organization():
    repo = OrganizationRepository(create_session())

    organization = repo.create(
        organization_id="org-1",
        name="Organization 1",
    )

    assert organization.id == "org-1"
    assert organization.name == "Organization 1"

    loaded = repo.get("org-1")

    assert loaded is not None
    assert loaded.id == "org-1"


def test_list_organizations():
    repo = OrganizationRepository(create_session())

    repo.create(
        organization_id="org-1",
        name="Organization 1",
    )
    repo.create(
        organization_id="org-2",
        name="Organization 2",
    )

    assert [
        organization.id
        for organization in repo.list()
    ] == ["org-1", "org-2"]
