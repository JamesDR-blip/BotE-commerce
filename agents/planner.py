from collections.abc import Sequence

from domain.plans import ExecutionPlan, PlanStep
from domain.dependency_resolver import DependencyResolver
from domain.capabilities import CapabilitySpec
from .requirement import ValidationRequirement
from .state import WorkflowState


class PlannerAgent:
    """Build deterministic execution plans from requested capabilities."""

    _VALIDATION_PLAN = (
        "requirements",
        "classify",
        "retrieve_rules",
        "extract",
        "autofix",
        "validate",
        "qa",
    )

    def __init__(
        self,
        catalog: dict[str, CapabilitySpec] | None = None,
        resolver: DependencyResolver | None = None,
    ) -> None:
        self._catalog = catalog or {}
        self._resolver = resolver or DependencyResolver()

    def plan(
        self,
        state: WorkflowState | ValidationRequirement,
    ):
        # Legacy LangGraph planner contract.
        if isinstance(state, dict):
            if not state["categories"]:
                raise ValueError("No validator categories are registered")

            return {"plan": self._VALIDATION_PLAN}

        # Capability-driven planner contract.
        requested = state.requested_capabilities

        specs = self._resolver.resolve(
            requested=requested,
            capabilities=self._catalog,
        )

        steps = tuple(
            PlanStep(
                capability_id=spec.id,
                capability_version=spec.version,
            )
            for spec in specs
        )

        return ExecutionPlan(
            steps=steps,
            metadata={"source": "planner"},
        )