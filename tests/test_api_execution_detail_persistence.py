from datetime import datetime, timezone

from fastapi.testclient import TestClient

from api.main import create_app
from configs.settings import Settings
from database.models import ExecutionRecord


def test_execution_detail_reads_real_persisted_data():
    client = TestClient(
        create_app(
            Settings(database_url="sqlite://")
        )
    )

    container = client.app.state.container

    container.executions.create(
        ExecutionRecord(
            id="exec-1",
            category="Fashion",
            source_hash="a" * 64,
            rule_version="1.0",
            health_score=95.0,
            status="COMPLETED",
            created_at=datetime.now(timezone.utc),
            requirement_json=(
                '{"requested_category":"Fashion"}'
            ),
            plan_json=(
                '{"version":"1.0","steps":[],"metadata":{}}'
            ),
            planner_version="planner-1",
        )
    )

    container.execution_traces.create(
        execution_id="exec-1",
        capability_id="data.validate",
        capability_version="1.0",
        status="COMPLETED",
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

    assert payload["requirement_json"] == (
        '{"requested_category":"Fashion"}'
    )

    assert payload["plan_json"] == (
        '{"version":"1.0","steps":[],"metadata":{}}'
    )

    assert payload["planner_version"] == "planner-1"

    assert len(payload["traces"]) == 1

    trace = payload["traces"][0]

    assert trace["capability_id"] == "data.validate"
    assert trace["capability_version"] == "1.0"
    assert trace["status"] == "COMPLETED"