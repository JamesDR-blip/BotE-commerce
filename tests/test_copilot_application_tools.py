from datetime import datetime, timezone

from application.copilot.application_tools import (
    CopilotApplicationTools,
    CopilotToolServices,
    build_copilot_tools,
)
from application.copilot.tool_definitions import (
    ExecuteWorkflowArguments,
    GetDatasetArguments,
    GetDiagnosticsArguments,
    GetHealthArguments,
    GetRemediationArguments,
    ListDatasetsArguments,
    SimulateWorkflowArguments,
)
from domain.identity import CurrentUser


class FakeDatasetService:
    def __init__(self):
        self.calls = []

    def list_datasets(self, **kwargs):
        self.calls.append(("list", kwargs))
        return ["dataset-1"]

    def get_dataset(self, **kwargs):
        self.calls.append(("get", kwargs))
        return {"id": kwargs["dataset_id"]}


class FakeHealth:
    def __init__(self):
        self.calls = []

    def get_health(self, **kwargs):
        self.calls.append(("health", kwargs))
        return "health"

    def get_diagnostics(self, **kwargs):
        self.calls.append(("diagnostics", kwargs))
        return ["diagnostic"]

    def get_remediation_proposals(self, **kwargs):
        self.calls.append(("remediation", kwargs))
        return ["proposal"]


class FakeSimulation:
    def __init__(self):
        self.calls = []

    def simulate(self, **kwargs):
        self.calls.append(kwargs)
        return "simulation"


class FakeExecutionStatus:
    def __init__(self, value):
        self.value = value


class FakeExecution:
    def __init__(
        self,
        execution_id="execution-1",
        status="COMPLETED",
        changeset_id="changeset-1",
    ):
        self.execution_id = execution_id
        self.status = FakeExecutionStatus(status)
        self.changeset_id = changeset_id


class FakeApproval:
    approval_id = "approval-1"
    execution_id = "execution-1"
    changeset_id = "changeset-1"
    risk_score = "HIGH"
    confidence_score = 0.85
    requested_by = "requester"
    created_at = datetime.now(timezone.utc)
    expires_at = None
    decision = None


class FakeApprovalService:
    def __init__(self, approval=None):
        self.approval = approval
        self.calls = []

    def get_for_execution(self, execution_id):
        self.calls.append(execution_id)
        return self.approval


class FakeRuntime:
    def __init__(self, execution=None):
        self.calls = []
        self.execution = execution or FakeExecution()

    def execute(self, **kwargs):
        self.calls.append(kwargs)
        return self.execution


def make_tools():
    datasets = FakeDatasetService()
    health = FakeHealth()
    simulation = FakeSimulation()
    runtime = FakeRuntime()
    approval = FakeApprovalService()

    services = CopilotToolServices(
        dataset_service=datasets,
        data_health=health,
        simulation_service=simulation,
        workflow_runtime=runtime,
        approval_service=approval,
    )

    tools = CopilotApplicationTools(services=services)

    return tools, datasets, health, simulation, runtime, approval


def test_read_tools_preserve_current_user_scope():
    tools, datasets, health, _, _, _ = make_tools()

    user = CurrentUser(
        user_id="owner-1",
        roles=frozenset(),
    )

    assert tools.list_datasets(
        current_user=user,
        arguments=ListDatasetsArguments(project_id="project-1"),
    ) == ["dataset-1"]

    assert tools.get_dataset(
        current_user=user,
        arguments=GetDatasetArguments(dataset_id="dataset-1"),
    ) == {"id": "dataset-1"}

    assert tools.get_health(
        current_user=user,
        arguments=GetHealthArguments(dataset_id="dataset-1"),
    ) == "health"

    assert tools.get_diagnostics(
        current_user=user,
        arguments=GetDiagnosticsArguments(dataset_id="dataset-1"),
    ) == ["diagnostic"]

    assert tools.get_remediation_proposals(
        current_user=user,
        arguments=GetRemediationArguments(dataset_id="dataset-1"),
    ) == ["proposal"]

    assert datasets.calls[0][1]["current_user"] == user
    assert datasets.calls[0][1]["project_id"] == "project-1"
    assert datasets.calls[1][1]["current_user"] == user
    assert health.calls[0][1]["owner_id"] == "owner-1"
    assert health.calls[1][1]["owner_id"] == "owner-1"
    assert health.calls[2][1]["owner_id"] == "owner-1"


def test_simulation_and_execution_use_governed_application_services():
    tools, _, _, simulation, runtime, _ = make_tools()

    user = CurrentUser(
        user_id="owner-1",
        roles=frozenset({"operator"}),
    )

    assert tools.simulate_workflow(
        current_user=user,
        arguments=SimulateWorkflowArguments(
            workflow_id="workflow-1",
            inputs={"frame": "input"},
            dataset_id="dataset-1",
        ),
    ) == "simulation"

    assert tools.execute_workflow(
        current_user=user,
        arguments=ExecuteWorkflowArguments(
            workflow_id="workflow-1",
            inputs={"frame": "input"},
            dataset_id="dataset-1",
        ),
    ) == {
        "execution_id": "execution-1",
        "status": "COMPLETED",
        "changeset_id": "changeset-1",
    }

    assert simulation.calls[0]["current_user"] == user
    assert runtime.calls[0]["current_user"] == user
    assert runtime.calls[0]["workflow_id"] == "workflow-1"


def test_tool_allowlist_contains_no_generic_execution_or_query_tool():
    tools, _, _, _, _, approval = make_tools()

    registry = build_copilot_tools(
        services=CopilotToolServices(
            dataset_service=tools._services.dataset_service,
            data_health=tools._services.data_health,
            simulation_service=tools._services.simulation_service,
            workflow_runtime=tools._services.workflow_runtime,
            approval_service=approval,
        ),
        author_workflow_handler=lambda **kwargs: kwargs,
    )

    assert registry.names() == (
        "list_datasets",
        "get_dataset",
        "get_health",
        "get_diagnostics",
        "get_remediation_proposals",
        "author_workflow",
        "simulate_workflow",
        "execute_workflow",
    )

    forbidden = {
        "execute_sql",
        "raw_sql",
        "python",
        "shell",
        "exec",
        "eval",
    }

    assert forbidden.isdisjoint(registry.names())


def test_pending_approval_returns_safe_approval_card_without_credentials():
    execution = FakeExecution(status="PENDING_APPROVAL")
    runtime = FakeRuntime(execution=execution)
    approval = FakeApprovalService(approval=FakeApproval())

    services = CopilotToolServices(
        dataset_service=FakeDatasetService(),
        data_health=FakeHealth(),
        simulation_service=FakeSimulation(),
        workflow_runtime=runtime,
        approval_service=approval,
    )
    tools = CopilotApplicationTools(services=services)

    result = tools.execute_workflow(
        current_user=CurrentUser(
            user_id="owner-1",
            roles=frozenset({"operator"}),
        ),
        arguments=ExecuteWorkflowArguments(
            workflow_id="workflow-1",
            inputs={"frame": "input"},
            dataset_id="dataset-1",
        ),
    )

    assert result["status"] == "PENDING_APPROVAL"
    assert result["changeset_id"] == "changeset-1"
    assert result["approval"]["approval_id"] == "approval-1"
    assert result["approval"]["execution_id"] == "execution-1"
    assert result["approval"]["changeset_id"] == "changeset-1"
    assert result["approval"]["risk_score"] == "HIGH"
    assert result["approval"]["confidence_score"] == 0.85
    assert "token" not in result["approval"]
    assert "token_hash" not in result["approval"]
    assert "secret" not in str(result).lower()
    assert approval.calls == ["execution-1"]


def test_completed_execution_does_not_lookup_approval():
    tools, _, _, _, _, approval = make_tools()

    result = tools.execute_workflow(
        current_user=CurrentUser(
            user_id="owner-1",
            roles=frozenset({"operator"}),
        ),
        arguments=ExecuteWorkflowArguments(
            workflow_id="workflow-1",
            inputs={"frame": "input"},
            dataset_id="dataset-1",
        ),
    )

    assert result["status"] == "COMPLETED"
    assert "approval" not in result
    assert approval.calls == []

