"""LangGraph builder that coordinates existing validation agents."""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from domain.models import ValidationResult
from plugins.registry import ValidatorRegistry

from .planner import PlannerAgent
from .state import WorkflowState
from .router import WorkflowRouter
from .workflow import Agents

from .nodes.requirement import RequirementNode
from .nodes.classifier import ClassifierNode
from .nodes.rule_retrieval import RuleRetrievalNode
from .nodes.extraction import ExtractionNode
from .nodes.autofix import AutoFixNode
from .nodes.validation import ValidationNode
from .nodes.qa import QANode

class WorkflowBuilder:
    """Build the validation graph while leaving domain work in existing agents."""

    def __init__(self, agents: Agents, registry: ValidatorRegistry, planner: PlannerAgent | None = None) -> None:
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
        self._graph = self.build()
        

    def build(self):
        graph = StateGraph(WorkflowState)
        graph.add_node("plan", self._planner.plan)
        graph.add_node("requirements", self._requirement_node)
        graph.add_node("classify", self._classifier_node)
        graph.add_node("retrieve_rules", self._rule_retrieval_node)
        graph.add_node("extract", self._extraction_node)
        graph.add_node("autofix", self._autofix_node)
        graph.add_node("validate", self._validation_node)
        graph.add_node("qa", self._qa_node)

        graph.add_edge(START, "plan")

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
        graph.add_edge("qa", END)
        
        return graph.compile()

    def run(self, frame, requested_category: str | None = None) -> ValidationResult:
        state = self._graph.invoke(
            {
                "frame": frame,
                "requested_category": requested_category,
                "categories": self._registry.categories(),
            }
        )
        return state["result"]
