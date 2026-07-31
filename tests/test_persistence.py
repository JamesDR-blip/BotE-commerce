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
    executions.save(
        ExecutionRecord(id="execution-1", user_id=user.id, category="Fashion", source_hash="hash", rule_version="1", health_score=87.5),
        [ValidationIssue(2, "Color", "missing_color", "Missing color")],
        {"json": "report.json"},
    )
    assert users.get_by_email("owner@example.com").id == user.id
    assert executions.history()[0].health_score == 87.5
    assert executions.get("execution-1").user_id == user.id
    assert executions.report_path("execution-1", "json") == "report.json"
