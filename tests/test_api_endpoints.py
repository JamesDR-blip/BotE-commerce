from fastapi.testclient import TestClient

from api.main import create_app
from configs.settings import Settings


def _client() -> TestClient:
    return TestClient(create_app(Settings(database_url="sqlite://")))


def test_upload_clean_extract_and_mapping_endpoints() -> None:
    client = _client()
    file = {"file": ("products.csv", b"product_title,Price\nPhilips HX-200 Blue 220V,100\n", "text/csv")}
    assert client.post("/upload", files=file).json()["rows"] == 1
    clean = client.post("/clean", files=file)
    assert clean.status_code == 200
    extracted = client.post("/extract", files=file)
    assert extracted.json()["records"][0]["attributes"]["brand"] == "Philips"
    mapped = client.post("/mapping", files=file)
    assert mapped.json()["mappings"]["product_title"] == "product_title"


def test_history_and_report_aliases_are_available() -> None:
    client = _client()
    class EmptyExecutions:
        def history(self, limit: int) -> list[object]:
            return []

        def report_path(self, execution_id: str, report_format: str) -> None:
            return None

    client.app.state.container.executions = EmptyExecutions()
    assert client.get("/history").status_code == 200
    assert client.get("/report/missing/json").status_code == 404
