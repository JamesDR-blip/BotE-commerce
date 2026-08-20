from services.container import build_container

def test_container_exposes_workflow_engine():

    container = build_container()

    assert container.workflow_engine is not None

    assert container.workflows is not None