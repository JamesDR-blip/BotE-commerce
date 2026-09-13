"""Application service for ephemeral workflow simulation."""

from __future__ import annotations

from typing import Any

from domain.identity import CurrentUser


class SimulationService:
    """Coordinate Shadow Mode without entering production execution flow."""

    def __init__(
        self,
        *,
        shadow_runner,
        workflows,
        datasets,
    ) -> None:
        self._shadow_runner = shadow_runner
        self._workflows = workflows
        self._datasets = datasets

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


