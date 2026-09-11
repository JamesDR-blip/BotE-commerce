from types import SimpleNamespace

from application.quality.data_health_service import DataHealthService
from domain.quality.data_health import HealthDimension


class FakeDatasets:
    def __init__(self, dataset):
        self.dataset = dataset

    def get_for_owner(self, *, dataset_id, owner_id):
        if owner_id != "owner-1":
            return None
        return self.dataset


class FakeExecutions:
    def __init__(self, executions, logs):
        self.executions = executions
        self.logs = logs

    def list_by_dataset(self, dataset_id):
        return self.executions

    def list_validation_logs(self, execution_id):
        return self.logs


def make_dataset():
    return SimpleNamespace(
        id="dataset-1",
        row_count=100,
        metadata={
            "profile": {
                "row_count": 100,
                "column_count": 2,
                "duplicate_row_count": 10,
                "columns": [
                    {"name": "name", "null_ratio": 0.0},
                    {"name": "price", "null_ratio": 0.2},
                ],
            }
        },
    )


def test_data_health_aggregates_profile_and_validation():
    execution = SimpleNamespace(
        id="execution-1",
        status="COMPLETED",
        health_score=80.0,
    )

    logs = [
        SimpleNamespace(
            code="missing_required",
            field="price",
            message="Required value is missing.",
            severity="error",
        ),
        SimpleNamespace(
            code="missing_required",
            field="price",
            message="Required value is missing.",
            severity="error",
        ),
    ]

    service = DataHealthService(
        datasets=FakeDatasets(make_dataset()),
        executions=FakeExecutions([execution], logs),
    )

    health = service.get_health(
        dataset_id="dataset-1",
        owner_id="owner-1",
    )

    assert health.metric(HealthDimension.COMPLETENESS).score == 90.0
    assert health.metric(HealthDimension.UNIQUENESS).score == 90.0
    assert health.metric(HealthDimension.VALIDITY).score == 80.0
    assert health.metric(HealthDimension.TIMELINESS).assessed is False


def test_diagnostics_are_grouped_without_row_numbers():
    execution = SimpleNamespace(
        id="execution-1",
        status="COMPLETED",
        health_score=80.0,
    )

    logs = [
        SimpleNamespace(
            code="invalid_price",
            field="price",
            message="Price must be positive.",
            severity="error",
        ),
        SimpleNamespace(
            code="invalid_price",
            field="price",
            message="Price must be positive.",
            severity="error",
        ),
    ]

    service = DataHealthService(
        datasets=FakeDatasets(make_dataset()),
        executions=FakeExecutions([execution], logs),
    )

    diagnostics = service.get_diagnostics(
        dataset_id="dataset-1",
        owner_id="owner-1",
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].count == 2
    assert not hasattr(diagnostics[0], "row_number")


def test_missing_or_wrong_owner_dataset_is_rejected():
    service = DataHealthService(
        datasets=FakeDatasets(make_dataset()),
        executions=FakeExecutions([], []),
    )

    try:
        service.get_health(
            dataset_id="dataset-1",
            owner_id="owner-2",
        )
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")
