from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from repositories.workflows import WorkflowRepository


def create_session():
    engine = create_engine("sqlite://")

    Base.metadata.create_all(engine)

    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


def test_workflow_version_lifecycle():

    repo = WorkflowRepository(
        create_session()
    )

    # create workflow
    workflow = repo.create(
        workflow_id="wf-1",
        project_id="project-1",
        name="Validation",
        version="1.0",
        plan_json="{}",
    )

    assert workflow.active_version == "1.0"


    # create new version
    version = repo.create_version(
        workflow_id="wf-1",
        version="2.0",
        plan_json='{"steps":["validate"]}',
    )

    assert version.version == "2.0"
    assert version.plan_json == '{"steps":["validate"]}'


    # list versions
    versions = repo.list_versions(
        "wf-1"
    )

    assert len(versions) == 2


    # activate version
    updated = repo.activate_version(
        "wf-1",
        "2.0",
    )

    assert updated.active_version == "2.0"


    # get active version
    active = repo.get_active_version(
        "wf-1"
    )

    assert active is not None
    assert active.version == "2.0"