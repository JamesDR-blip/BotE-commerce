from fastapi.testclient import TestClient
from api.main import create_app
from configs.settings import Settings

def test_health_endpoint(tmp_path) -> None:
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}", reports_path=tmp_path / "reports"))
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_validation_upload_generates_all_reports(tmp_path) -> None:
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}", reports_path=tmp_path / "reports"))
    response = TestClient(app).post(
        "/validations",
        files={"file": ("fashion.csv", b"Size,Color,Price\ns, Red ,100\n", "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "Fashion"
    assert set(body["reports"]) == {"excel", "html", "json", "pdf"}
