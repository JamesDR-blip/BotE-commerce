from fastapi.testclient import TestClient

from api.main import create_app
from unittest.mock import patch
from configs.settings import Settings
from datetime import datetime, timezone


def _client() -> TestClient:
    return TestClient(
        create_app(Settings(database_url="sqlite://")), 
        raise_server_exceptions=False,
    )


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


def test_validate_rejects_unsupported_category() -> None:
    client = _client()

    file = {
        "file": (
            "products.csv",
            b"product_title,Price\nPhilips HX-200 Blue 220V,100\n",
            "text/csv",
        )
    }

    response = client.post(
        "/validate",
        files=file,
        data={"category": "UnsupportedCategory"},
    )

    assert response.status_code == 422
    assert "Unsupported category" in response.json()["detail"]


def test_validate_does_not_convert_unexpected_error_to_422() -> None:
    client = _client()

    file = {
        "file": (
            "products.csv",
            b"product_title,Price\nPhilips HX-200 Blue 220V,100\n",
            "text/csv",
        )
    }

    with patch.object(
        client.app.state.quality_service,
        "validate",
        side_effect=RuntimeError("unexpected failure"),
    ):
        response = client.post(
            "/validate",
            files=file,
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}


def test_unexpected_error_is_logged_without_exposing_details(caplog) -> None:
    client = _client()

    file = {
        "file": (
            "products.csv",
            b"product_title,Price\nPhilips HX-200 Blue 220V,100\n",
            "text/csv",
        )
    }

    with caplog.at_level("ERROR"), patch.object(
        client.app.state.quality_service,
        "validate",
        side_effect=RuntimeError("secret internal failure"),
    ):
        response = client.post("/validate", files=file)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "secret internal failure" not in response.text
    assert "unexpected_application_error" in caplog.text



def test_validate_uses_real_capability_pipeline() -> None:
    client = _client()

    file = {
        "file": (
            "products.csv",
            (
                b"product_title,Price\n"
                b"Nike Air Max 90,100\n"
                b"Adidas Ultraboost,120\n"
            ),
            "text/csv",
        )
    }

    response = client.post(
        "/validate",
        files=file,
        data={"category": "Fashion"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["execution_id"]
    assert payload["category"] == "Fashion"
    assert isinstance(payload["health_score"], (int, float))
    assert isinstance(payload["reports"], dict)
    assert payload["cached"] is False


def test_execution_detail_returns_execution_and_traces() -> None:
    client = _client()

    execution = client.app.state.container.executions.get(
        "missing"
    )

    assert execution is None

    class FakeExecution:
        id = "exec-1"
        category = "Fashion"
        status = "COMPLETED"
        health_score = 95.0
        created_at = datetime.now(timezone.utc)
        requirement_json = '{"requested_category":"Fashion"}'
        plan_json = '{"steps":[]}'
        planner_version = "planner-1"

    class FakeTrace:
        capability_id = "data.validate"
        capability_version = "1.0"
        status = "COMPLETED"
        started_at = datetime.now(timezone.utc)
        finished_at = datetime.now(timezone.utc)

    class FakeExecutions:
        def get(self, execution_id):
            if execution_id == "exec-1":
                return FakeExecution()
            return None

    class FakeTraces:
        def list_by_execution(self, execution_id):
            return [FakeTrace()]

    client.app.state.container.workflow_history.executions = (
        FakeExecutions()
    )
    client.app.state.container.workflow_history.traces = (
        FakeTraces()
    )

    response = client.get(
        "/executions/exec-1"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["execution_id"] == "exec-1"
    assert payload["category"] == "Fashion"
    assert payload["status"] == "COMPLETED"
    assert payload["health_score"] == 95.0
    assert payload["planner_version"] == "planner-1"

    assert len(payload["traces"]) == 1
    assert payload["traces"][0]["capability_id"] == "data.validate"
    assert payload["traces"][0]["status"] == "COMPLETED"


def test_execution_detail_returns_404_for_missing_execution() -> None:
    client = _client()

    class EmptyExecutions:
        def get(self, execution_id):
            return None

    class EmptyTraces:
        def list_by_execution(self, execution_id):
            return []

    client.app.state.container.workflow_history.executions = (
        EmptyExecutions()
    )
    client.app.state.container.workflow_history.traces = (
        EmptyTraces()
    )

    response = client.get(
        "/executions/missing"
    )

    assert response.status_code == 404
    assert "Execution not found" in response.json()["detail"]