from configs.settings import Settings
from services.container import Container
from application.datasets.dataset_ingestion import DatasetIngestionService


def test_container_exposes_workflow_authoring_service():

    settings = Settings(
        database_url="sqlite://"
    )

    container = Container(settings)

    assert container.workflow_authoring is not None
    assert isinstance(
        container.dataset_ingestion,
        DatasetIngestionService,
    )
