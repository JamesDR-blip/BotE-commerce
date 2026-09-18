from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from application.copilot.approval import CopilotApprovalCard

from application.copilot.tool_definitions import (
    AuthorWorkflowArguments,
    ExecuteWorkflowArguments,
    GetDatasetArguments,
    GetDiagnosticsArguments,
    GetHealthArguments,
    GetRemediationArguments,
    ListDatasetsArguments,
    SimulateWorkflowArguments,
)
from application.copilot.tools import CopilotTool, CopilotToolRegistry
from domain.identity import CurrentUser


@dataclass(frozen=True)
class CopilotToolServices:
    dataset_service: Any
    data_health: Any
    simulation_service: Any
    workflow_runtime: Any
    approval_service: Any | None = None


class CopilotApplicationTools:
    """Typed, owner-scoped application tools exposed to Copilot."""

    def __init__(
        self,
        *,
        services: CopilotToolServices,
    ) -> None:
        self._services = services

    def list_datasets(
        self,
        *,
        current_user: CurrentUser,
        arguments: ListDatasetsArguments,
    ) -> Any:
        return self._services.dataset_service.list_datasets(
            current_user=current_user,
            project_id=arguments.project_id,
        )

    def get_dataset(
        self,
        *,
        current_user: CurrentUser,
        arguments: GetDatasetArguments,
    ) -> Any:
        return self._services.dataset_service.get_dataset(
            current_user=current_user,
            dataset_id=arguments.dataset_id,
        )

    def get_health(
        self,
        *,
        current_user: CurrentUser,
        arguments: GetHealthArguments,
    ) -> Any:
        return self._services.data_health.get_health(
            dataset_id=arguments.dataset_id,
            owner_id=current_user.user_id,
        )

    def get_diagnostics(
        self,
        *,
        current_user: CurrentUser,
        arguments: GetDiagnosticsArguments,
    ) -> Any:
        return self._services.data_health.get_diagnostics(
            dataset_id=arguments.dataset_id,
            owner_id=current_user.user_id,
        )

    def get_remediation_proposals(
        self,
        *,
        current_user: CurrentUser,
        arguments: GetRemediationArguments,
    ) -> Any:
        return self._services.data_health.get_remediation_proposals(
            dataset_id=arguments.dataset_id,
            owner_id=current_user.user_id,
        )

    def simulate_workflow(
        self,
        *,
        current_user: CurrentUser,
        arguments: SimulateWorkflowArguments,
    ) -> Any:
        return self._services.simulation_service.simulate(
            workflow_id=arguments.workflow_id,
            current_user=current_user,
            inputs=arguments.inputs,
            dataset_id=arguments.dataset_id,
        )

    def execute_workflow(
        self,
        *,
        current_user: CurrentUser,
        arguments: ExecuteWorkflowArguments,
    ) -> Any:
        execution = self._services.workflow_runtime.execute(
            current_user=current_user,
            workflow_id=arguments.workflow_id,
            inputs=arguments.inputs,
            dataset_id=arguments.dataset_id,
        )

        result = {
            "execution_id": execution.execution_id,
            "status": execution.status.value,
            "changeset_id": execution.changeset_id,
        }

        if execution.status.value == "PENDING_APPROVAL":
            approval = self._services.approval_service.get_for_execution(
                execution.execution_id,
            )

            if approval is None:
                raise RuntimeError(
                    "Pending approval was not found for workflow execution"
                )

            result["approval"] = (
                CopilotApprovalCard.from_record(approval).to_dict()
            )

        return result


def build_copilot_tools(
    *,
    services: CopilotToolServices,
    author_workflow_handler: Callable[..., Any],
) -> CopilotToolRegistry:
    """Build the fixed Copilot application allowlist."""

    tools = CopilotApplicationTools(services=services)

    return CopilotToolRegistry(
        tools=(
            CopilotTool(
                name="list_datasets",
                description="List datasets in an owned project.",
                handler=tools.list_datasets,
                arguments_type=ListDatasetsArguments,
            ),
            CopilotTool(
                name="get_dataset",
                description="Read one owned dataset.",
                handler=tools.get_dataset,
                arguments_type=GetDatasetArguments,
            ),
            CopilotTool(
                name="get_health",
                description="Read health for one owned dataset.",
                handler=tools.get_health,
                arguments_type=GetHealthArguments,
            ),
            CopilotTool(
                name="get_diagnostics",
                description="Read diagnostics for one owned dataset.",
                handler=tools.get_diagnostics,
                arguments_type=GetDiagnosticsArguments,
            ),
            CopilotTool(
                name="get_remediation_proposals",
                description="Read remediation proposals for one owned dataset.",
                handler=tools.get_remediation_proposals,
                arguments_type=GetRemediationArguments,
            ),
            CopilotTool(
                name="author_workflow",
                description="Author a deterministic workflow plan without executing it.",
                handler=author_workflow_handler,
                arguments_type=AuthorWorkflowArguments,
            ),
            CopilotTool(
                name="simulate_workflow",
                description="Simulate an owned workflow without production execution.",
                handler=tools.simulate_workflow,
                arguments_type=SimulateWorkflowArguments,
            ),
            CopilotTool(
                name="execute_workflow",
                description="Request execution through the governed workflow runtime.",
                handler=tools.execute_workflow,
                arguments_type=ExecuteWorkflowArguments,
            ),
        )
    )

