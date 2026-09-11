from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, ExecutionRecord
from domain.models import ValidationIssue
from repositories.executions import ExecutionRepository
from repositories.users import UserRepository


def test_user_and_execution_repositories_persist_history_reports_scores_and_logs() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    users = UserRepository(sessions)
    executions = ExecutionRepository(sessions)
    user = users.create("owner@example.com", "Owner")
    executions.create(
        ExecutionRecord(
            id="execution-1",
            user_id=user.id,
            category="Fashion",
            source_hash="hash",
            rule_version="1",
            health_score=0.0,
            status="RUNNING",
        )
    )

    executions.save_result(
        execution_id="execution-1",
        category="Fashion",
        source_hash="hash",
        rule_version="1",
        health_score=87.5,
        issues=[
            ValidationIssue(
                2,
                "Color",
                "missing_color",
                "Missing color",
            )
        ],
        reports={"json": "report.json"},
    )
    assert users.get_by_email("owner@example.com").id == user.id
    assert executions.history()[0].health_score == 87.5
    assert executions.get("execution-1").user_id == user.id
    assert executions.report_path("execution-1", "json") == "report.json"


def test_execution_repository_lists_executions_by_dataset() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    repository = ExecutionRepository(sessions)

    repository.create(
        ExecutionRecord(
            id="dataset-a-old",
            dataset_id="dataset-a",
            category="Fashion",
            source_hash="a" * 64,
            rule_version="1",
            health_score=80.0,
            status="COMPLETED",
        )
    )
    repository.create(
        ExecutionRecord(
            id="dataset-b",
            dataset_id="dataset-b",
            category="Fashion",
            source_hash="b" * 64,
            rule_version="1",
            health_score=70.0,
            status="COMPLETED",
        )
    )
    repository.create(
        ExecutionRecord(
            id="dataset-a-new",
            dataset_id="dataset-a",
            category="Fashion",
            source_hash="c" * 64,
            rule_version="1",
            health_score=90.0,
            status="COMPLETED",
        )
    )

    executions = repository.list_by_dataset("dataset-a")

    assert [record.id for record in executions] == [
        "dataset-a-new",
        "dataset-a-old",
    ]

    limited = repository.list_by_dataset("dataset-a", limit=1)

    assert [record.id for record in limited] == ["dataset-a-new"]

def test_execution_repository_updates_status() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    repository = ExecutionRepository(sessions)
    
    record = ExecutionRecord(
        id="test-execution",
        category="Fashion",
        source_hash="a" * 64,
        rule_version="1",
        health_score=0.0,
        status="RUNNING",
    )

    repository.create(record)

    stored = repository.get("test-execution")

    assert stored is not None
    assert stored.status == "RUNNING"

    repository.update_status(
        "test-execution",
        "COMPLETED",
    )

    stored = repository.get("test-execution")

    assert stored is not None
    assert stored.status == "COMPLETED"


def test_execution_repository_updates_status_to_failed() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    repository = ExecutionRepository(sessions)

    record = ExecutionRecord(
        id="failed-execution",
        category="Fashion",
        source_hash="b" * 64,
        rule_version="1",
        health_score=0.0,
        status="RUNNING",
    )

    repository.create(record)

    repository.update_status(
        "failed-execution",
        "FAILED",
    )

    stored = repository.get("failed-execution")

    assert stored is not None
    assert stored.status == "FAILED"

def test_execution_repository_persists_execution_context() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    repository = ExecutionRepository(sessions)

    record = ExecutionRecord(
        id="context-execution",
        category="Fashion",
        source_hash="c" * 64,
        rule_version="1",
        health_score=0.0,
        status="RUNNING",
    )

    repository.create(record)

    repository.save_execution_context(
        "context-execution",
        requirement_json='{"requested_category":"Fashion"}',
        plan_json='{"version":"1.0","steps":[]}',
        planner_version="1.0",
    )

    stored = repository.get("context-execution")

    assert stored is not None
    assert stored.requirement_json == (
        '{"requested_category":"Fashion"}'
    )
    assert stored.plan_json == (
        '{"version":"1.0","steps":[]}'
    )
    assert stored.planner_version == "1.0"


def test_execution_repository_rejects_missing_execution_context() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    repository = ExecutionRepository(sessions)

    try:
        repository.save_execution_context(
            "missing-execution",
            requirement_json="{}",
            plan_json="{}",
            planner_version="1.0",
        )
    except ValueError as exc:
        assert "missing-execution" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for missing execution"
        )

def test_execution_repository_persists_and_reads_execution_context() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    sessions = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    repository = ExecutionRepository(sessions)

    repository.create(
        ExecutionRecord(
            id="context-execution",
            category="Fashion",
            source_hash="a" * 64,
            rule_version="1",
            health_score=0.0,
            status="RUNNING",
        )
    )

    repository.save_execution_context(
        "context-execution",
        requirement_json='{"requested_category":"Fashion"}',
        plan_json='{"version":"1.0","steps":[],"metadata":{}}',
        planner_version="planner-1",
    )

    context = repository.execution_context(
        "context-execution"
    )

    assert context is not None
    assert context["requirement_json"] == (
        '{"requested_category":"Fashion"}'
    )
    assert context["plan_json"] == (
        '{"version":"1.0","steps":[],"metadata":{}}'
    )
    assert context["planner_version"] == "planner-1"
