from collections.abc import Sequence

from domain.plans import ExecutionPlan, PlanStep
from domain.dependency_resolver import DependencyResolver
from domain.capabilities import CapabilitySpec
from domain.capability_registry import CapabilityRegistry

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
        registry: CapabilityRegistry | None = None,
        resolver: DependencyResolver | None = None,
        catalog: dict[str, CapabilitySpec] | None = None,
    ) -> None:
        if registry is not None and catalog is not None:
            raise ValueError(
                "PlannerAgent accepts either registry or catalog, not both"
            )

        self._registry = registry
        self._catalog = catalog
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

        if self._registry is not None:
            capabilities = self._registry.catalog()
        elif self._catalog is not None:
            capabilities = self._catalog
        else:
            raise ValueError(
                "Planner requires a capability registry or catalog"
            )

        specs = self._resolver.resolve(
            requested=requested,
            capabilities=capabilities,
        )

        requirement_mappings = state.input_mappings or {}
        requirement_parameters = state.parameters or {}

        steps = tuple(
            PlanStep(
                capability_id=spec.id,
                capability_version=spec.version,
                parameters=dict(
                    requirement_parameters.get(spec.id, {})
                ),
                input_mapping=dict(
                    requirement_mappings.get(
                        spec.id, 
                        dict(spec.input_mappings),
                    )
                ),
            )
            for spec in specs
        )

        return ExecutionPlan(
            steps=steps,
            metadata={"source": "planner"},
        )