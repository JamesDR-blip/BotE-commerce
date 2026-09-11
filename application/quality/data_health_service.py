"""Read-only application service for dataset health aggregation."""

from __future__ import annotations

from collections import Counter
from typing import Any
from uuid import uuid4

from domain.quality.data_health import (
    DataHealthScore,
    HealthDimension,
    HealthMetric,
    IssueDiagnostic,
    RemediationProposal,
    completeness_score,
    uniqueness_score,
)


class DataHealthService:
    """Aggregate persisted dataset/profile/validation health signals."""

    def __init__(self, *, datasets, executions) -> None:
        self._datasets = datasets
        self._executions = executions

    def get_health(
        self,
        *,
        dataset_id: str,
        owner_id: str,
    ) -> DataHealthScore:
        dataset = self._datasets.get_for_owner(
            dataset_id=dataset_id,
            owner_id=owner_id,
        )

        if dataset is None:
            raise KeyError(f"Dataset not found: {dataset_id}")

        profile = self._profile(dataset.metadata)

        null_ratios = tuple(
            float(column.get("null_ratio", 0.0))
            for column in profile.get("columns", [])
        )

        completeness = completeness_score(null_ratios)

        row_count = int(
            profile.get(
                "row_count",
                dataset.row_count or 0,
            )
        )
        duplicate_row_count = int(
            profile.get("duplicate_row_count", 0)
        )

        uniqueness = uniqueness_score(
            row_count,
            duplicate_row_count,
        )

        executions = self._executions.list_by_dataset(dataset_id)

        completed = [
            execution
            for execution in executions
            if execution.status == "COMPLETED"
        ]

        latest = completed[0] if completed else None

        validity = (
            HealthMetric(
                HealthDimension.VALIDITY,
                self._clamp(latest.health_score),
            )
            if latest is not None
            else HealthMetric(
                HealthDimension.VALIDITY,
                0.0,
                assessed=False,
            )
        )

        logs = (
            self._executions.list_validation_logs(latest.id)
            if latest is not None
            else []
        )

        consistency = self._consistency_metric(logs)

        return DataHealthScore(
            metrics=(
                HealthMetric(
                    HealthDimension.COMPLETENESS,
                    completeness,
                ),
                validity,
                HealthMetric(
                    HealthDimension.UNIQUENESS,
                    uniqueness,
                ),
                consistency,
                HealthMetric(
                    HealthDimension.TIMELINESS,
                    0.0,
                    assessed=False,
                ),
            )
        )

    def get_health_metrics(
        self,
        *,
        project_id: str,
        owner_id: str,
    ) -> list[tuple[Any, DataHealthScore]]:
        datasets = self._datasets.list_by_project_for_owner(
            project_id=project_id,
            owner_id=owner_id,
        )

        return [
            (
                dataset,
                self.get_health(
                    dataset_id=dataset.id,
                    owner_id=owner_id,
                ),
            )
            for dataset in datasets
        ]

    def get_diagnostics(
        self,
        *,
        dataset_id: str,
        owner_id: str,
    ) -> list[IssueDiagnostic]:
        dataset = self._datasets.get_for_owner(
            dataset_id=dataset_id,
            owner_id=owner_id,
        )

        if dataset is None:
            raise KeyError(f"Dataset not found: {dataset_id}")

        executions = self._executions.list_by_dataset(dataset_id)

        completed = [
            execution
            for execution in executions
            if execution.status == "COMPLETED"
        ]

        if not completed:
            return []

        logs = self._executions.list_validation_logs(
            completed[0].id
        )

        grouped: Counter[tuple[str, str, str, str]] = Counter(
            (
                log.code,
                log.field,
                log.severity,
                log.message,
            )
            for log in logs
        )

        return [
            IssueDiagnostic(
                code=code,
                field=field,
                message=message,
                severity=severity,
                count=count,
            )
            for (code, field, severity, message), count
            in grouped.items()
        ]

    def get_remediation_proposals(
        self,
        *,
        dataset_id: str,
        owner_id: str,
    ) -> list[RemediationProposal]:
        diagnostics = self.get_diagnostics(
            dataset_id=dataset_id,
            owner_id=owner_id,
        )

        return [
            RemediationProposal(
                id=str(uuid4()),
                diagnostic_code=diagnostic.code,
                action=self._remediation_action(diagnostic.code),
                rationale=diagnostic.message,
                severity=diagnostic.severity,
            )
            for diagnostic in diagnostics
        ]

    @staticmethod
    def _profile(metadata: dict[str, Any]) -> dict[str, Any]:
        profile = metadata.get("profile", {})
        return profile if isinstance(profile, dict) else {}

    @staticmethod
    def _clamp(value: float) -> float:
        return round(max(0.0, min(100.0, float(value))), 2)

    @classmethod
    def _consistency_metric(cls, logs) -> HealthMetric:
        if not logs:
            return HealthMetric(
                HealthDimension.CONSISTENCY,
                100.0,
                assessed=True,
            )

        weights = {
            "error": 1.0,
            "warning": 0.5,
            "info": 0.1,
        }

        penalty = sum(
            weights.get(str(log.severity).lower(), 0.5)
            for log in logs
        )

        score = cls._clamp(
            100.0 / (1.0 + penalty / max(len(logs), 1))
        )

        return HealthMetric(
            HealthDimension.CONSISTENCY,
            score,
            assessed=True,
        )

    @staticmethod
    def _remediation_action(code: str) -> str:
        return f"review_{code}_issues"


__all__ = ["DataHealthService"]
