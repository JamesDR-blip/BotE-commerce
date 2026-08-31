from configs.settings import Settings
from services.container import Container
from services.dataset_ingestion import DatasetIngestionService


def test_container_exposes_studio_service():

    settings = Settings(
        database_url="sqlite://"
    )

    container = Container(settings)

    assert container.studio is not None
    assert isinstance(
        container.dataset_ingestion,
        DatasetIngestionService,
    )