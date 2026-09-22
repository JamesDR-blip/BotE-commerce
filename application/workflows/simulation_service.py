"""Application service for ephemeral workflow simulation."""

from __future__ import annotations

from typing import Any

from domain.identity import CurrentUser
from services.authorization import AuthorizationService


class SimulationService:
    """Coordinate Shadow Mode without entering production execution flow."""

    def __init__(
        self,
        *,
        shadow_runner,
        workflows,
        datasets,
        projects=None,
        workspaces=None,
        authorization: AuthorizationService | None = None,
    ) -> None:
        self._shadow_runner = shadow_runner
        self._workflows = workflows
        self._datasets = datasets
        self._projects = projects
        self._workspaces = workspaces
        self._authorization = authorization

    def _organization_id_for_workflow(
        self,
        *,
        workflow,
        owner_id: str,
    ) -> str | None:
        if self._authorization is None:
            return None

        if self._projects is None or self._workspaces is None:
            raise RuntimeError(
                "Project and workspace repositories are required for simulation authorization"
            )

        project = self._projects.get_for_owner(
            project_id=workflow.project_id,
            owner_id=owner_id,
        )
        if project is None:
            raise ValueError(
                f"Project not found: {workflow.project_id}"
            )

        workspace = self._workspaces.get_for_owner(
            workspace_id=project.workspace_id,
            owner_id=owner_id,
        )
        if workspace is None:
            raise ValueError(
                f"Workspace not found: {project.workspace_id}"
            )

        return workspace.organization_id

    def _authorize(
        self,
        *,
        current_user: CurrentUser,
        organization_id: str | None,
    ) -> None:
        if self._authorization is None or organization_id is None:
            return

        self._authorization.authorize(
            user=current_user,
            resource="workflow",
            action="read",
            organization_id=organization_id,
        )

    def simulate(
        self,
        *,
        workflow_id: str,
        current_user: CurrentUser,
        inputs: dict[str, Any] | None = None,
        dataset_id: str | None = None,
        max_diff_rows: int = 100,
    ):
        workflow = self._workflows.get_for_owner(
            workflow_id=workflow_id,
            owner_id=current_user.user_id,
        )

        if workflow is None:
            raise ValueError(
                f"Workflow not found: {workflow_id}"
            )

        organization_id = self._organization_id_for_workflow(
            workflow=workflow,
            owner_id=current_user.user_id,
        )
        self._authorize(
            current_user=current_user,
            organization_id=organization_id,
        )

        dataset = None

        if dataset_id is not None:
            dataset = self._datasets.get_for_owner(
                dataset_id=dataset_id,
                owner_id=current_user.user_id,
            )

            if dataset is None:
                raise ValueError(
                    f"Dataset not found: {dataset_id}"
                )

            if dataset.project_id != workflow.project_id:
                raise ValueError(
                    f"Dataset does not belong to workflow project: "
                    f"{dataset_id}"
                )

        version = self._workflows.get_active_version(workflow_id)

        if version is None:
            raise ValueError(
                f"Workflow has no active version: {workflow_id}"
            )

        plan = self._deserialize_plan(version.plan_json)

        return self._shadow_runner.simulate(
            workflow_id=workflow_id,
            workflow_version=version.version,
            plan=plan,
            inputs=dict(inputs or {}),
            dataset=dataset,
            max_diff_rows=max_diff_rows,
        )

    @staticmethod
    def _deserialize_plan(plan_json):
        import json

        from domain.plans import ExecutionPlan, PlanStep

        if isinstance(plan_json, ExecutionPlan):
            return plan_json

        if isinstance(plan_json, str):
            plan_json = json.loads(plan_json)

        steps = tuple(
            PlanStep(
                capability_id=step["capability_id"],
                capability_version=step.get(
                    "capability_version",
                    "1.0",
                ),
                parameters=step.get(
                    "parameters",
                    {},
                ),
                input_mapping=step.get(
                    "input_mapping",
                    {},
                ),
            )
            for step in plan_json.get("steps", [])
        )

        return ExecutionPlan(
            steps=steps,
            version=plan_json.get("version", "1.0"),
            metadata=plan_json.get("metadata", {}),
        )


__all__ = ["SimulationService"]


