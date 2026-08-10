"""LangGraph builder that coordinates existing validation agents."""
from __future__ import annotations

import logging
from uuid import uuid4

from langgraph import graph
from langgraph.graph import END, START, StateGraph

from domain.models import ValidationResult
from plugins.registry import ValidatorRegistry

from .planner import PlannerAgent
from .state import WorkflowState
from .router import WorkflowRouter
from .workflow import Agents
from .observability import observe_node

from .nodes.requirement import RequirementNode
from .nodes.classifier import ClassifierNode
from .nodes.rule_retrieval import RuleRetrievalNode
from .nodes.extraction import ExtractionNode
from .nodes.autofix import AutoFixNode
from .nodes.validation import ValidationNode
from .nodes.qa import QANode
from .nodes.execution import (
    ExecutionStartNode,
    ExecutionCompleteNode,
)


logger = logging.getLogger(__name__)


class WorkflowBuilder:
    """Build the validation graph while leaving domain work in existing agents."""

    def __init__(
        self, 
        agents: Agents, 
        registry: ValidatorRegistry, 
        planner: PlannerAgent | None = None,
    ) -> None:
        self._agents = agents
        self._registry = registry
        self._planner = planner or PlannerAgent()
        self._requirement_node = RequirementNode(self._agents.requirements)
        self._classifier_node = ClassifierNode(self._agents.classifier)
        self._rule_retrieval_node = RuleRetrievalNode(self._agents.rules)
        self._extraction_node = ExtractionNode(self._agents.extraction)
        self._autofix_node = AutoFixNode(self._agents.fixer, self._registry)
        self._validation_node = ValidationNode(self._agents.validator, self._registry)
        self._qa_node = QANode(self._agents.qa)
        self._router = WorkflowRouter()
        self._execution_start_node = ExecutionStartNode()
        self._execution_complete_node = ExecutionCompleteNode()
        self._graph = self.build()
        
        

    def build(self):
        graph = StateGraph(WorkflowState)

        graph.add_node(
            "plan",
            observe_node("plan", self._planner.plan),
        )

        graph.add_node(
            "requirements",
            observe_node("requirements", self._requirement_node),
        )

        graph.add_node(
            "classify",
            observe_node("classify", self._classifier_node),
        )

        graph.add_node(
            "retrieve_rules",
            observe_node("retrieve_rules", self._rule_retrieval_node),
        )

        graph.add_node(
            "extract",
            observe_node("extract", self._extraction_node),
        )

        graph.add_node(
            "autofix",
            observe_node("autofix", self._autofix_node),
        )

        graph.add_node(
            "validate",
            observe_node("validate", self._validation_node),
        )

        graph.add_node(
            "qa",
            observe_node("qa", self._qa_node),
        )
        graph.add_node("execution_start", self._execution_start_node)
        graph.add_node("execution_complete", self._execution_complete_node)

        graph.add_edge(START, "execution_start")
        graph.add_edge("execution_start", "plan")

        graph.add_conditional_edges(
            "plan",
            self._router.route,
            {
                "validation": "requirements",
            },
        )

        graph.add_edge("requirements", "classify")
        graph.add_edge("classify", "retrieve_rules")
        graph.add_edge("retrieve_rules", "extract")
        graph.add_edge("extract", "autofix")
        graph.add_edge("autofix", "validate")
        graph.add_edge("validate", "qa")
        graph.add_edge("qa", "execution_complete")
        graph.add_edge("execution_complete", END)

        return graph.compile()

    def run(
        self,
        frame,
        requested_category: str | None = None,
        execution_id: str | None = None,
    ) -> ValidationResult:
        execution_id = execution_id or str(uuid4())

        logger.info(
            "workflow_started",
            extra={
                "event": "workflow_started",
                "execution_id": execution_id,
                "workflow": "validation",
            },
        )

        try:
            state = self._graph.invoke(
                {
                    "frame": frame,
                    "execution_id": execution_id,
                    "workflow": "validation",
                    "execution_status": "RUNNING",
                    "requested_category": requested_category,
                    "categories": self._registry.categories(),
                }
            )

            result = state["result"]

            logger.info(
                "workflow_completed",
                extra={
                    "event": "workflow_completed",
                    "execution_id": execution_id,
                    "workflow": "validation",
                    "category": result.category,
                    "status": "COMPLETED",
                },
            )

            return result

        except Exception:
            logger.exception(
                "workflow_failed",
                extra={
                    "event": "workflow_failed",
                    "execution_id": execution_id,
                    "workflow": "validation",
                    "status": "FAILED",
                },
            )
            raise
