from domain.plans import ExecutionPlan
from domain.studio import (
    Workspace,
    Project,
    Dataset,
    Workflow,
)


def test_workspace_creation():
    workspace = Workspace(
        id="ws-1",
        name="Demo Workspace",
    )

    assert workspace.id == "ws-1"


def test_project_belongs_to_workspace():
    project = Project(
        id="project-1",
        workspace_id="ws-1",
        name="Nike Catalog",
    )

    assert project.workspace_id == "ws-1"


def test_dataset_belongs_to_project():
    dataset = Dataset(
        id="dataset-1",
        project_id="project-1",
        name="catalog.csv",
        source_type="upload",
        metadata={},
    )

    assert dataset.project_id == "project-1"


def test_workflow_contains_execution_plan():

    plan = ExecutionPlan(
        steps=(),
        version="1.0",
        metadata={},
    )

    workflow = Workflow(
        id="workflow-1",
        project_id="project-1",
        name="Validate Catalog",
        version="1",
        plan=plan,
    )

    assert workflow.plan.version == "1.0"