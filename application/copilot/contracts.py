from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CopilotAction:
    """Validated action proposed by the Copilot."""

    action: str
    arguments: dict[str, Any] = field(default_factory=dict)
    call_id: str | None = None


@dataclass(frozen=True)
class CopilotResponse:
    """Normalized response returned by the Copilot."""

    message: str
    actions: tuple[CopilotAction, ...] = ()


@dataclass(frozen=True)
class CopilotTextEvent:
    """Provider-neutral conversational text event."""

    role: str
    content: str
    kind: str = "text"


@dataclass(frozen=True)
class CopilotToolCallEvent:
    """Provider-neutral tool-call event."""

    action: CopilotAction
    kind: str = "tool_call"


@dataclass(frozen=True)
class CopilotToolResultEvent:
    """Provider-neutral tool-result event."""

    action: CopilotAction
    result: Any
    kind: str = "tool_result"


@dataclass(frozen=True)
class CopilotApprovalEvent:
    """Safe approval metadata exposed by the Copilot stream."""

    approval: dict[str, Any]
    kind: str = "approval"


CopilotEvent = (
    CopilotTextEvent
    | CopilotToolCallEvent
    | CopilotToolResultEvent
)
