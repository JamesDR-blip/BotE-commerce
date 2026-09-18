from __future__ import annotations

from typing import Any

from agents.planner import PlannerAgent
from agents.requirement import RequirementAgent
from application.copilot.approval import CopilotApprovalCard
from application.copilot.contracts import (
    CopilotAction,
    CopilotApprovalEvent,
    CopilotResponse,
)
from application.copilot.sessions import CopilotSession, CopilotSessionStore
from application.copilot.tools import CopilotToolRegistry
from domain.identity import CurrentUser


class CopilotService:
    """Application orchestration boundary for Copilot interactions."""

    def __init__(
        self,
        *,
        requirements: RequirementAgent,
        planner: PlannerAgent,
        tools: CopilotToolRegistry,
        projects: Any,
        agent: Any | None = None,
        session_store: CopilotSessionStore | None = None,
    ) -> None:
        self._requirements = requirements
        self._planner = planner
        self._tools = tools
        self._projects = projects
        self._agent = agent
        self._session_store = session_store or CopilotSessionStore()

    def create_session(self, *, current_user: CurrentUser) -> CopilotSession:
        return self._session_store.create(current_user=current_user)

    def get_session(
        self,
        *,
        current_user: CurrentUser,
        session_id: str,
    ) -> CopilotSession:
        return self._session_store.get(
            current_user=current_user,
            session_id=session_id,
        )

    def append_session_turn(
        self,
        *,
        current_user: CurrentUser,
        session_id: str,
        role: str,
        content: str,
    ) -> CopilotSession:
        return self._session_store.append_turn(
            current_user=current_user,
            session_id=session_id,
            role=role,
            content=content,
        )

    def append_session_action(
        self,
        *,
        current_user: CurrentUser,
        session_id: str,
        action: CopilotAction,
    ) -> CopilotSession:
        return self._session_store.append_action(
            current_user=current_user,
            session_id=session_id,
            action=action,
        )

    def append_session_tool_result(
        self,
        *,
        current_user: CurrentUser,
        session_id: str,
        action: CopilotAction,
        result: object,
    ) -> CopilotSession:
        return self._session_store.append_tool_result(
            current_user=current_user,
            session_id=session_id,
            action=action,
            result=result,
        )

    def author_workflow(
        self,
        *,
        current_user: CurrentUser,
        project_id: str,
        name: str,
        user_request: str,
    ) -> CopilotResponse:
        project = self._projects.get_for_owner(
            project_id=project_id,
            owner_id=current_user.user_id,
        )
        if project is None:
            raise ValueError(f"Project not found: {project_id}")

        requirement = self._requirements.interpret(
            user_request=user_request,
            workspace_id=None,
            user_id=current_user.user_id,
        )

        plan = self._planner.plan(requirement)

        return CopilotResponse(
            message="Workflow plan authored successfully.",
            actions=(
                CopilotAction(
                    action="workflow_plan",
                    arguments={
                        "project_id": project_id,
                        "name": name,
                        "requirement": requirement,
                        "plan": plan,
                    },
                ),
            ),
        )

    def respond(
        self,
        *,
        current_user: CurrentUser,
        user_message: str,
    ) -> CopilotResponse:
        """Generate a Copilot response and execute one proposed tool action."""
        if self._agent is None:
            raise RuntimeError("CopilotAgent is not configured")

        response = self._agent.respond(user_message)

        if not response.actions:
            return response

        if len(response.actions) > 1:
            raise ValueError("Copilot currently supports one tool action per turn")

        action = response.actions[0]

        tool_result = self.invoke_tool(
            current_user=current_user,
            tool_name=action.action,
            arguments=action.arguments,
        )

        return self._agent.respond_with_tool_result(
            user_message=user_message,
            action=action,
            tool_result=tool_result,
        )
    def stream(
        self,
        *,
        current_user: CurrentUser,
        user_message: str,
        session_id: str | None = None,
    ):
        """Stream Copilot output and execute one proposed tool action."""
        if self._agent is None:
            raise RuntimeError("CopilotAgent is not configured")

        history = None

        if session_id is not None:
            session = self.get_session(
                current_user=current_user,
                session_id=session_id,
            )
            history = session.events

            self.append_session_turn(
                current_user=current_user,
                session_id=session_id,
                role="user",
                content=user_message,
            )

        action = None

        for chunk in self._agent.stream(
            user_message,
            history=history,
        ):
            if isinstance(chunk, CopilotAction):
                if action is not None:
                    raise ValueError(
                        "Copilot currently supports one tool action per turn"
                    )
                action = chunk

                if session_id is not None:
                    self.append_session_action(
                        current_user=current_user,
                        session_id=session_id,
                        action=action,
                    )
                continue

            if session_id is not None:
                self.append_session_turn(
                    current_user=current_user,
                    session_id=session_id,
                    role="assistant",
                    content=chunk,
                )

            yield chunk

        if action is None:
            return

        tool_result = self.invoke_tool(
            current_user=current_user,
            tool_name=action.action,
            arguments=action.arguments,
        )

        if session_id is not None:
            self.append_session_tool_result(
                current_user=current_user,
                session_id=session_id,
                action=action,
                result=tool_result,
            )

        if (
            isinstance(tool_result, dict)
            and tool_result.get("status") == "PENDING_APPROVAL"
            and isinstance(tool_result.get("approval"), dict)
        ):
            approval = tool_result["approval"]
            yield CopilotApprovalEvent(
                approval=CopilotApprovalCard(
                    approval_id=approval["approval_id"],
                    execution_id=approval["execution_id"],
                    changeset_id=approval["changeset_id"],
                    risk_score=approval["risk_score"],
                    confidence_score=approval["confidence_score"],
                    requested_by=approval["requested_by"],
                    created_at=__import__("datetime").datetime.fromisoformat(
                        approval["created_at"]
                    ),
                    expires_at=(
                        __import__("datetime").datetime.fromisoformat(
                            approval["expires_at"]
                        )
                        if approval["expires_at"] is not None
                        else None
                    ),
                    status=approval["status"],
                ).to_dict()
            )

        final_response = self._agent.respond_with_tool_result(
            user_message=user_message,
            action=action,
            tool_result=tool_result,
            history=history,
        )

        if final_response.message:
            if session_id is not None:
                self.append_session_turn(
                    current_user=current_user,
                    session_id=session_id,
                    role="assistant",
                    content=final_response.message,
                )

            yield final_response.message
    def invoke_tool(
        self,
        *,
        current_user: CurrentUser,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Invoke one explicitly registered and typed application tool."""

        return self._tools.invoke(
            tool_name,
            arguments,
            current_user=current_user,
        )


