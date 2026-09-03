from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowRequirement:
    """Validated workflow requirement."""

    requested_category: str | None = None
    requested_capabilities: tuple[str, ...] = ()
    requested_intents: tuple[str, ...] = ()
    input_mappings: dict[str, dict[str, str]] | None = None
    parameters: dict[str, dict[str, object]] | None = None


ValidationRequirement = WorkflowRequirement