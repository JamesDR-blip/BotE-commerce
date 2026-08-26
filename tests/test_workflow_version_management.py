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

def test_workflow_version_cannot_be_created_twice():
    repo = WorkflowRepository(
        create_session()
    )

    repo.create(
        workflow_id="wf-duplicate",
        project_id="project-1",
        name="Validation",
        version="1.0",
        plan_json='{"stage":"initial"}',
    )

    repo.create_version(
        workflow_id="wf-duplicate",
        version="2.0",
        plan_json='{"stage":"v2"}',
    )

    try:
        repo.create_version(
            workflow_id="wf-duplicate",
            version="2.0",
            plan_json='{"stage":"duplicate"}',
        )
    except ValueError as exc:
        assert str(exc) == (
            "Workflow version already exists: "
            "wf-duplicate@2.0"
        )
    else:
        raise AssertionError(
            "Expected duplicate workflow version to fail"
        )

    version = repo.get_version(
        "wf-duplicate",
        "2.0",
    )

    assert version is not None
    assert version.plan_json == '{"stage":"v2"}'