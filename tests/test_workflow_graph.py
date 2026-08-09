import pandas as pd
import pytest
import logging
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


def test_workflow_logs_started_and_completed(caplog) -> None:
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

    builder = WorkflowBuilder(
        agents,
        ValidatorRegistry(),
    )

    execution_id = "test-execution-123"

    with caplog.at_level(logging.INFO, logger="agents.graph"):
        result = builder.run(
            pd.DataFrame(
                {
                    "Size": ["s"],
                    "Color": [" Red "],
                    "Price": ["100"],
                }
            ),
            execution_id=execution_id,
        )

    events = [
        record.__dict__.get("event")
        for record in caplog.records
    ]

    assert "workflow_started" in events
    assert "workflow_completed" in events

    started = next(
        record for record in caplog.records
        if record.__dict__.get("event") == "workflow_started"
    )

    completed = next(
        record for record in caplog.records
        if record.__dict__.get("event") == "workflow_completed"
    )

    assert started.__dict__["execution_id"] == execution_id
    assert completed.__dict__["execution_id"] == execution_id
    assert completed.__dict__["category"] == "Fashion"
    assert result.category == "Fashion"


def test_workflow_logs_failed_execution(caplog, monkeypatch) -> None:
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

    builder = WorkflowBuilder(
        agents,
        ValidatorRegistry(),
    )

    execution_id = "test-failed-execution"

    def fail(*args, **kwargs):
        raise RuntimeError("forced workflow failure")

    monkeypatch.setattr(builder._graph, "invoke", fail)

    with caplog.at_level(logging.INFO, logger="agents.graph"):
        with pytest.raises(RuntimeError, match="forced workflow failure"):
            builder.run(
                pd.DataFrame(
                    {
                        "Size": ["s"],
                        "Color": [" Red "],
                        "Price": ["100"],
                    }
                ),
                execution_id=execution_id,
            )

    failed = next(
        record
        for record in caplog.records
        if record.__dict__.get("event") == "workflow_failed"
    )

    assert failed.__dict__["execution_id"] == execution_id
    assert failed.__dict__["workflow"] == "validation"


def test_workflow_propagates_execution_context() -> None:
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

    builder = WorkflowBuilder(
        agents,
        ValidatorRegistry(),
    )

    execution_id = "test-execution-001"

    state = builder._graph.invoke(
        {
            "frame": pd.DataFrame(
                {
                    "Size": ["s"],
                    "Color": [" Red "],
                    "Price": ["100"],
                }
            ),
            "execution_id": execution_id,
            "workflow": "validation",
            "requested_category": None,
            "categories": builder._registry.categories(),
        }
    )

    assert state["execution_id"] == execution_id
    assert state["workflow"] == "validation"
    assert state["execution_status"] == "COMPLETED"


def test_workflow_marks_execution_completed() -> None:
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

    builder = WorkflowBuilder(
        agents,
        ValidatorRegistry(),
    )

    execution_id = "test-execution-completed"

    state = builder._graph.invoke(
        {
            "frame": pd.DataFrame(
                {
                    "Size": ["s"],
                    "Color": [" Red "],
                    "Price": ["100"],
                }
            ),
            "execution_id": execution_id,
            "workflow": "validation",
            "requested_category": None,
            "categories": builder._registry.categories(),
        }
    )

    assert state["execution_id"] == execution_id
    assert state["workflow"] == "validation"
    assert state["execution_status"] == "COMPLETED"

def test_execution_lifecycle_nodes() -> None:
    from agents.nodes.execution import (
        ExecutionStartNode,
        ExecutionCompleteNode,
        ExecutionFailedNode,
    )

    state = {
        "execution_id": "test-execution-001",
        "workflow": "validation",
    }

    started = ExecutionStartNode()(state)

    assert started["execution_status"] == "RUNNING"
    assert started["workflow"] == "validation"

    completed = ExecutionCompleteNode()(
        {**state, **started}
    )

    assert completed["execution_status"] == "COMPLETED"

    failed = ExecutionFailedNode()(
        {**state, **started}
    )

    assert failed["execution_status"] == "FAILED"