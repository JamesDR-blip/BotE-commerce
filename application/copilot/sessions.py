from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from application.copilot.contracts import (
    CopilotAction,
    CopilotEvent,
    CopilotTextEvent,
    CopilotToolCallEvent,
    CopilotToolResultEvent,
)
from domain.identity import CurrentUser


@dataclass(frozen=True)
class CopilotSession:
    session_id: str
    owner_id: str
    events: tuple[CopilotEvent, ...] = ()

    @property
    def turns(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            (event.role, event.content)
            for event in self.events
            if isinstance(event, CopilotTextEvent)
        )


class CopilotSessionStore:
    """Process-local store for Copilot conversation sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, CopilotSession] = {}

    def create(self, *, current_user: CurrentUser) -> CopilotSession:
        session = CopilotSession(
            session_id=str(uuid4()),
            owner_id=current_user.user_id,
        )
        self._sessions[session.session_id] = session
        return session

    def get(
        self,
        *,
        current_user: CurrentUser,
        session_id: str,
    ) -> CopilotSession:
        session = self._sessions.get(session_id)
        if session is None or session.owner_id != current_user.user_id:
            raise ValueError("Copilot session not found")
        return session

    def append_turn(
        self,
        *,
        current_user: CurrentUser,
        session_id: str,
        role: str,
        content: str,
    ) -> CopilotSession:
        return self._append(
            current_user=current_user,
            session_id=session_id,
            event=CopilotTextEvent(role=role, content=content),
        )

    def append_action(
        self,
        *,
        current_user: CurrentUser,
        session_id: str,
        action: CopilotAction,
    ) -> CopilotSession:
        return self._append(
            current_user=current_user,
            session_id=session_id,
            event=CopilotToolCallEvent(action=action),
        )

    def append_tool_result(
        self,
        *,
        current_user: CurrentUser,
        session_id: str,
        action: CopilotAction,
        result: object,
    ) -> CopilotSession:
        return self._append(
            current_user=current_user,
            session_id=session_id,
            event=CopilotToolResultEvent(
                action=action,
                result=result,
            ),
        )

    def _append(
        self,
        *,
        current_user: CurrentUser,
        session_id: str,
        event: CopilotEvent,
    ) -> CopilotSession:
        session = self.get(
            current_user=current_user,
            session_id=session_id,
        )
        updated = CopilotSession(
            session_id=session.session_id,
            owner_id=session.owner_id,
            events=session.events + (event,),
        )
        self._sessions[session.session_id] = updated
        return updated
