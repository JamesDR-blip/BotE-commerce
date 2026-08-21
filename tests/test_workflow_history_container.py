from configs.settings import Settings
from services.container import Container


def test_container_exposes_workflow_history():

    settings = Settings(
        database_url="sqlite://"
    )

    container = Container(settings)

    assert container.workflow_history is not None