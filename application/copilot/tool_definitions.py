from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ListDatasetsArguments:
    project_id: str


@dataclass(frozen=True)
class GetDatasetArguments:
    dataset_id: str


@dataclass(frozen=True)
class GetHealthArguments:
    dataset_id: str


@dataclass(frozen=True)
class GetDiagnosticsArguments:
    dataset_id: str


@dataclass(frozen=True)
class GetRemediationArguments:
    dataset_id: str


@dataclass(frozen=True)
class AuthorWorkflowArguments:
    project_id: str
    name: str
    user_request: str


@dataclass(frozen=True)
class SimulateWorkflowArguments:
    workflow_id: str
    inputs: dict[str, Any]
    dataset_id: str | None = None


@dataclass(frozen=True)
class ExecuteWorkflowArguments:
    workflow_id: str
    inputs: dict[str, Any]
    dataset_id: str | None = None


@dataclass(frozen=True)
class CopilotToolSet:
    """Explicit application-level Copilot tool allowlist."""

    list_datasets: Any
    get_dataset: Any
    get_health: Any
    get_diagnostics: Any
    get_remediation_proposals: Any
    author_workflow: Any
    simulate_workflow: Any
    execute_workflow: Any

    def as_tuple(self) -> tuple[Any, ...]:
        return (
            self.list_datasets,
            self.get_dataset,
            self.get_health,
            self.get_diagnostics,
            self.get_remediation_proposals,
            self.author_workflow,
            self.simulate_workflow,
            self.execute_workflow,
        )
