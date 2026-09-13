from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from application.workflows.simulation_service import SimulationService
from domain.identity import CurrentUser
from domain.plans import ExecutionPlan


def _service(*, workflow=None, dataset=None, active_version=None):
    workflows = Mock()
    datasets = Mock()
    runner = Mock()

    workflows.get_for_owner.return_value = workflow
    workflows.get_active_version.return_value = active_version
    datasets.get_for_owner.return_value = dataset

    return (
        SimulationService(
            shadow_runner=runner,
            workflows=workflows,
            datasets=datasets,
        ),
        workflows,
        datasets,
        runner,
    )


def _workflow(project_id="project-1"):
    return SimpleNamespace(
        id="workflow-1",
        project_id=project_id,
    )


def _version(version="1.0"):
    return SimpleNamespace(
        version=version,
        plan_json={
            "steps": [],
            "version": "1.0",
        },
    )


def test_simulate_uses_owner_scoped_workflow_lookup():
    service, workflows, datasets, runner = _service(
        workflow=_workflow(),
        active_version=_version(),
    )

    service.simulate(
        workflow_id="workflow-1",
        current_user=CurrentUser(user_id="user-1"),
    )

    workflows.get_for_owner.assert_called_once_with(
        workflow_id="workflow-1",
        owner_id="user-1",
    )
    runner.simulate.assert_called_once()
    datasets.get_for_owner.assert_not_called()


def test_simulate_rejects_workflow_outside_owner_scope():
    service, workflows, datasets, runner = _service(
        workflow=None,
    )

    with pytest.raises(
        ValueError,
        match="Workflow not found: workflow-1",
    ):
        service.simulate(
            workflow_id="workflow-1",
            current_user=CurrentUser(user_id="user-1"),
        )

    runner.simulate.assert_not_called()


def test_simulate_rejects_dataset_from_different_project():
    service, workflows, datasets, runner = _service(
        workflow=_workflow(project_id="project-1"),
        dataset=SimpleNamespace(
            id="dataset-1",
            project_id="project-2",
        ),
        active_version=_version(),
    )

    with pytest.raises(
        ValueError,
        match="Dataset does not belong to workflow project",
    ):
        service.simulate(
            workflow_id="workflow-1",
            current_user=CurrentUser(user_id="user-1"),
            dataset_id="dataset-1",
        )

    datasets.get_for_owner.assert_called_once_with(
        dataset_id="dataset-1",
        owner_id="user-1",
    )
    runner.simulate.assert_not_called()


def test_simulate_uses_active_version_and_does_not_create_execution():
    service, workflows, datasets, runner = _service(
        workflow=_workflow(),
        active_version=_version(version="2.0"),
    )

    service.simulate(
        workflow_id="workflow-1",
        current_user=CurrentUser(user_id="user-1"),
        inputs={"value": 10},
    )

    workflows.get_active_version.assert_called_once_with(
        "workflow-1"
    )

    kwargs = runner.simulate.call_args.kwargs

    assert kwargs["workflow_id"] == "workflow-1"
    assert kwargs["workflow_version"] == "2.0"
    assert isinstance(kwargs["plan"], ExecutionPlan)
    assert kwargs["inputs"] == {"value": 10}
    assert kwargs["dataset"] is None

