from pathlib import Path
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from database.models import Base, ExecutionRecord
from domain.models import ValidationIssue
from repositories.executions import ExecutionRepository
from repositories.users import UserRepository
from database.models import make_session_factory
from configs.settings import Settings


def _verify_database_lifecycle_contract(monkeypatch, tmp_path) -> None:
    alembic_config = Config(
        str(Path(__file__).resolve().parents[1] / "alembic.ini")
    )
    alembic_config.set_main_option("path_separator", "os")
    current_head = ScriptDirectory.from_config(alembic_config).get_current_head()
    assert current_head == "20261002_01"

    # Fresh test/development databases use metadata creation and are usable
    # immediately by the repository layer.
    fresh_path = tmp_path / "fresh-dev.sqlite"
    fresh_sessions = make_session_factory(f"sqlite:///{fresh_path}")
    assert {"datasets", "workflow_executions"} <= set(
        inspect(fresh_sessions.kw["bind"]).get_table_names()
    )
    from repositories.workflow_executions import WorkflowExecutionRepository

    assert WorkflowExecutionRepository(fresh_sessions).get("not-created") is None

    # A production connection must be Alembic-managed and at the current head;
    # an empty/unversioned database is rejected without creating tables.
    unversioned_path = tmp_path / "unversioned.sqlite"
    try:
        make_session_factory(
            f"sqlite:///{unversioned_path}",
            create_schema=False,
            require_current_revision=True,
        )
    except RuntimeError as exc:
        assert "must be upgraded with Alembic" in str(exc)
    else:
        raise AssertionError("unversioned production database was accepted")
    assert inspect(create_engine(f"sqlite:///{unversioned_path}")).get_table_names() == []

    # Current Alembic-managed schema is accepted without metadata mutation.
    managed_path = tmp_path / "managed.sqlite"
    managed_engine = create_engine(f"sqlite:///{managed_path}")
    Base.metadata.create_all(managed_engine)
    with managed_engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"
        )
        connection.exec_driver_sql(
            "INSERT INTO alembic_version (version_num) VALUES (?)",
            (current_head,),
        )
    original_tables = set(inspect(managed_engine).get_table_names())
    managed_sessions = make_session_factory(
        f"sqlite:///{managed_path}",
        create_schema=False,
        require_current_revision=True,
    )
    assert set(inspect(managed_sessions.kw["bind"]).get_table_names()) == original_tables

    # Prove the active clean-install path from an empty database.
    clean_path = tmp_path / "clean-install.sqlite"
    clean_url = f"sqlite:///{clean_path}"
    monkeypatch.setenv("DATABASE_URL", clean_url)
    command.upgrade(alembic_config, "head")
    clean_engine = create_engine(clean_url)
    with clean_engine.connect() as connection:
        assert MigrationContext.configure(connection).get_current_revision() == current_head
    assert {
        "alembic_version",
        "organizations",
        "datasets",
        "workflow_executions",
        "channels",
        "changesets",
    } <= set(inspect(clean_engine).get_table_names())

    # API and worker share Container startup policy: no create_all in
    # production; both require the already-migrated current revision.
    startup_path = tmp_path / "production.sqlite"
    startup_engine = create_engine(f"sqlite:///{startup_path}")
    Base.metadata.create_all(startup_engine)
    with startup_engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"
        )
        connection.exec_driver_sql(
            "INSERT INTO alembic_version (version_num) VALUES (?)",
            (current_head,),
        )

    import services.container as container_module

    startup_url = f"sqlite:///{startup_path}"
    calls = []

    def startup_sessions(url, **kwargs):
        calls.append((url, kwargs))
        return make_session_factory(startup_url, **kwargs)

    monkeypatch.setattr(container_module, "make_session_factory", startup_sessions)
    settings = Settings(
        environment="production",
        database_url="postgresql+psycopg://user:pass@db/app",
        workflow_queue_backend="redis",
        redis_url="redis://localhost:6379/0",
    )
    from api.main import create_app
    from worker import create_workflow_consumer

    app = create_app(settings)
    consumer = create_workflow_consumer(settings)
    assert app.state.container.workflow_worker is not None
    assert consumer._recovery_worker.__name__ == "recover"
    assert calls == [
        (settings.database_url, {"create_schema": False, "require_current_revision": True}),
        (settings.database_url, {"create_schema": False, "require_current_revision": True}),
    ]


def test_user_and_execution_repositories_persist_history_reports_scores_and_logs(
    monkeypatch,
    tmp_path,
) -> None:
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
    _verify_database_lifecycle_contract(monkeypatch, tmp_path)


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
