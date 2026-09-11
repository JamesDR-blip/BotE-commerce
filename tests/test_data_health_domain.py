from domain.quality.data_health import (
    DataHealthScore,
    HealthDimension,
    HealthMetric,
    IssueDiagnostic,
    RemediationProposal,
    completeness_score,
    uniqueness_score,
)


def test_completeness_score_uses_average_null_ratio():
    assert completeness_score((0.0, 0.1, 0.2)) == 90.0


def test_uniqueness_score_uses_duplicate_row_ratio():
    assert uniqueness_score(100, 5) == 95.0


def test_health_aggregate_ignores_unassessed_dimensions():
    score = DataHealthScore(
        metrics=(
            HealthMetric(
                HealthDimension.COMPLETENESS,
                90.0,
            ),
            HealthMetric(
                HealthDimension.VALIDITY,
                80.0,
            ),
            HealthMetric(
                HealthDimension.TIMELINESS,
                0.0,
                assessed=False,
            ),
        )
    )

    assert score.aggregate == 85.0


def test_health_metric_rejects_invalid_score():
    try:
        HealthMetric(HealthDimension.COMPLETENESS, 101.0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_diagnostic_and_remediation_are_sanitized_models():
    diagnostic = IssueDiagnostic(
        code="missing_required",
        field="price",
        message="Required value is missing.",
        severity="error",
        count=3,
    )
    proposal = RemediationProposal(
        id="proposal-1",
        diagnostic_code=diagnostic.code,
        action="review_missing_price_values",
        rationale="Required price values are missing.",
        severity="error",
    )

    assert diagnostic.count == 3
    assert proposal.status == "PROPOSED"
