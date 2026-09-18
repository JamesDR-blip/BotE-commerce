from application.copilot.tool_definitions import (
    AuthorWorkflowArguments,
    CopilotToolSet,
    ExecuteWorkflowArguments,
    GetDatasetArguments,
    GetDiagnosticsArguments,
    GetHealthArguments,
    GetRemediationArguments,
    ListDatasetsArguments,
    SimulateWorkflowArguments,
)
from application.copilot.tools import CopilotTool


def test_typed_argument_contracts():
    assert ListDatasetsArguments(project_id="p").project_id == "p"
    assert GetDatasetArguments(dataset_id="d").dataset_id == "d"
    assert GetHealthArguments(dataset_id="d").dataset_id == "d"
    assert GetDiagnosticsArguments(dataset_id="d").dataset_id == "d"
    assert GetRemediationArguments(dataset_id="d").dataset_id == "d"

    author = AuthorWorkflowArguments(
        project_id="p",
        name="workflow",
        user_request="clean products",
    )
    assert author.user_request == "clean products"

    simulation = SimulateWorkflowArguments(
        workflow_id="w",
        inputs={"frame": "input"},
    )
    assert simulation.dataset_id is None

    execution = ExecuteWorkflowArguments(
        workflow_id="w",
        inputs={"frame": "input"},
        dataset_id="d",
    )
    assert execution.dataset_id == "d"


def test_tool_set_contains_only_explicitly_allowed_operations():
    tool = CopilotTool(
        name="test",
        description="test",
        handler=lambda: None,
    )

    tool_set = CopilotToolSet(
        list_datasets=tool,
        get_dataset=tool,
        get_health=tool,
        get_diagnostics=tool,
        get_remediation_proposals=tool,
        author_workflow=tool,
        simulate_workflow=tool,
        execute_workflow=tool,
    )

    assert tool_set.as_tuple() == (
        tool,
        tool,
        tool,
        tool,
        tool,
        tool,
        tool,
        tool,
    )
