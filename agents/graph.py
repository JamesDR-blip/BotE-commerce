"""LangGraph builder that coordinates existing validation agents."""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from domain.models import ValidationResult
from plugins.registry import ValidatorRegistry

from .planner import PlannerAgent
from .state import WorkflowState
from .workflow import Agents


class WorkflowBuilder:
    """Build the validation graph while leaving domain work in existing agents."""

    def __init__(self, agents: Agents, registry: ValidatorRegistry, planner: PlannerAgent | None = None) -> None:
        self._agents = agents
        self._registry = registry
        self._planner = planner or PlannerAgent()

    def build(self):
        graph = StateGraph(WorkflowState)
        graph.add_node("plan", self._planner.plan)
        graph.add_node("requirements", self._requirements)
        graph.add_node("classify", self._classify)
        graph.add_node("retrieve_rules", self._retrieve_rules)
        graph.add_node("extract", self._extract)
        graph.add_node("autofix", self._autofix)
        graph.add_node("validate", self._validate)
        graph.add_node("qa", self._qa)
        graph.add_edge(START, "plan")
        graph.add_edge("plan", "requirements")
        graph.add_edge("requirements", "classify")
        graph.add_edge("classify", "retrieve_rules")
        graph.add_edge("retrieve_rules", "extract")
        graph.add_edge("extract", "autofix")
        graph.add_edge("autofix", "validate")
        graph.add_edge("validate", "qa")
        graph.add_edge("qa", END)
        return graph.compile()

    def run(self, frame, requested_category: str | None = None) -> ValidationResult:
        state = self.build().invoke(
            {"frame": frame, "requested_category": requested_category, "categories": self._registry.categories()}
        )
        return state["result"]

    def _classify(self, state: WorkflowState) -> dict[str, str]:
        return {"category": self._agents.classifier.classify(state["frame"], state["categories"], state["requirement"].requested_category)}

    def _requirements(self, state: WorkflowState) -> dict[str, object]:
        return {"requirement": self._agents.requirements.interpret(state.get("requested_category"))}

    def _retrieve_rules(self, state: WorkflowState) -> dict[str, object]:
        rules, version = self._agents.rules.retrieve(state["category"])
        return {"rules": rules, "rule_version": version}

    def _autofix(self, state: WorkflowState) -> dict[str, object]:
        validator = self._registry.get(state["category"])
        return {"fixed_frame": self._agents.fixer.fix(state["frame"], validator)}

    def _extract(self, state: WorkflowState) -> dict[str, object]:
        return {"extractions": self._agents.extraction.extract(state["frame"])}

    def _validate(self, state: WorkflowState) -> dict[str, object]:
        validator = self._registry.get(state["category"])
        return {"issues": self._agents.validator.validate(state["fixed_frame"], validator, state["rules"])}

    def _qa(self, state: WorkflowState) -> dict[str, ValidationResult]:
        return {"result": self._agents.qa.result(state["fixed_frame"], state["issues"], state["category"], state["rule_version"])}
