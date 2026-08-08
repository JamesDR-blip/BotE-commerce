import pandas as pd
from pathlib import Path

from agents.graph import WorkflowBuilder
from agents.planner import PlannerAgent
from agents.workflow import Agents, AutoFixAgent, ClassifierAgent, QAAgent, RuleRetrieverAgent, ValidatorAgent
from agents.requirement import RequirementAgent
from agents.extraction import ExtractionAgent
from extractors.deterministic import DeterministicProductExtractor
from plugins.registry import ValidatorRegistry
from repositories.rules import RuleRepository
from services.health_score_service import HealthScoreService
from services.validation_service import ValidationService
from unittest.mock import patch


def test_planner_declares_the_validation_orchestration() -> None:
    plan = PlannerAgent().plan({"categories": ["Fashion"]})
    assert plan["plan"] == ("requirements", "classify", "retrieve_rules", "extract", "autofix", "validate", "qa")


def test_workflow_builder_preserves_validation_result() -> None:
    agents = Agents(
        RequirementAgent(), ClassifierAgent(), RuleRetrieverAgent(RuleRepository(Path("rules_library.yaml"))), ExtractionAgent(DeterministicProductExtractor()), AutoFixAgent(),
        ValidatorAgent(ValidationService()), QAAgent(HealthScoreService()),
    )
    result = WorkflowBuilder(agents, ValidatorRegistry()).run(pd.DataFrame({"Size": ["s"], "Color": [" Red "], "Price": ["100"]}))
    assert result.category == "Fashion"
    assert result.clean.iloc[0]["Size"] == "S"
    assert result.health_score == 100.0


def test_workflow_builder_compiles_graph_once() -> None:
    agents = Agents(
        RequirementAgent(),
        ClassifierAgent(),
        RuleRetrieverAgent(
            RuleRepository(Path("rules_library.yaml"))
        ),
        ExtractionAgent(
            DeterministicProductExtractor()
        ),
        AutoFixAgent(),
        ValidatorAgent(ValidationService()),
        QAAgent(HealthScoreService()),
    )

    original_build = WorkflowBuilder.build

    with patch.object(
        WorkflowBuilder,
        "build",
        autospec=True,
        side_effect=original_build,
    ) as build_mock:
        builder = WorkflowBuilder(
            agents,
            ValidatorRegistry(),
        )

        assert build_mock.call_count == 1

        frame = pd.DataFrame(
            {
                "Size": ["s"],
                "Color": [" Red "],
                "Price": ["100"],
            }
        )

        builder.run(frame)
        builder.run(frame)

        assert build_mock.call_count == 1