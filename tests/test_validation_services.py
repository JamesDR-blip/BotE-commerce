import pandas as pd

from domain.validation.duplicates import DuplicateDetection
from domain.validation.format import FormatValidation
from domain.quality.health_score import HealthScoreService
from services.missing_value_validation import MissingValueValidation


def test_health_score_preserves_existing_formula() -> None:
    assert HealthScoreService().calculate(3, 4) == 75.0
    assert HealthScoreService().calculate(0, 0) == 0.0


def test_duplicate_detection_uses_normalized_exact_titles() -> None:
    issues = DuplicateDetection().normalized_text_duplicates(pd.Series([" Fan ", "fan", "Other"]), "product_title", "duplicate_product", "Duplicate normalized product title")
    assert [(issue.row, issue.code) for issue in issues] == [(3, "duplicate_product")]


def test_missing_and_format_services_keep_issue_shapes() -> None:
    frame = pd.DataFrame({"value": ["0", "two"]})
    missing = MissingValueValidation().missing_column(frame, "color", "missing_column", "Missing required column: color")
    invalid = FormatValidation().positive_number(frame["value"], "Price", "invalid_price", "Price must be a positive number")
    assert [issue.row for issue in missing] == [2, 3]
    assert [issue.code for issue in invalid] == ["invalid_price", "invalid_price"]


