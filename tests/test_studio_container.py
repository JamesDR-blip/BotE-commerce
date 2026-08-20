from configs.settings import Settings
from services.container import Container


def test_container_exposes_studio_service():

    settings = Settings(
        database_url="sqlite://"
    )

    container = Container(settings)

    assert container.studio is not None