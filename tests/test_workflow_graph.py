import pandas as pd
from pathlib import Path

from agents.graph import WorkflowBuilder
from agents.planner import PlannerAgent
from agents.workflow import Agents, AutoFixAgent, ClassifierAgent, QAAgent, RuleRetrieverAgent, ValidatorAgent
from agents.requirement import RequirementAgent
from plugins.registry import ValidatorRegistry
from repositories.rules import RuleRepository
from services.health_score_service import HealthScoreService
from services.validation_service import ValidationService


def test_planner_declares_the_validation_orchestration() -> None:
    plan = PlannerAgent().plan({"categories": ["Fashion"]})
    assert plan["plan"] == ("requirements", "classify", "retrieve_rules", "autofix", "validate", "qa")


def test_workflow_builder_preserves_validation_result() -> None:
    agents = Agents(
        RequirementAgent(), ClassifierAgent(), RuleRetrieverAgent(RuleRepository(Path("rules_library.yaml"))), AutoFixAgent(),
        ValidatorAgent(ValidationService()), QAAgent(HealthScoreService()),
    )
    result = WorkflowBuilder(agents, ValidatorRegistry()).run(pd.DataFrame({"Size": ["s"], "Color": [" Red "], "Price": ["100"]}))
    assert result.category == "Fashion"
    assert result.clean.iloc[0]["Size"] == "S"
    assert result.health_score == 100.0
