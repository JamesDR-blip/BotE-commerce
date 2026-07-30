from pathlib import Path

import pandas as pd
import pytest

from rule_engine.loader import RuleLoader
from rule_engine.parser import RuleParser
from rule_engine.validator import RuleValidator


def test_loader_parses_fashion_rules() -> None:
    rules, version = RuleLoader(Path("rules_library.yaml")).get("Fashion")
    assert len(version) == 12
    assert [rule.type for rule in rules.rules] == ["required_column", "required_column", "required_column", "positive_number", "enum", "non_empty"]


def test_rule_validator_applies_fashion_rule_definitions() -> None:
    rules, _ = RuleLoader(Path("rules_library.yaml")).get("Fashion")
    frame = pd.DataFrame({"Price": ["0"], "Size": ["BAD"], "Color": [" "]})
    assert [issue.code for issue in RuleValidator().validate(frame, rules)] == ["invalid_price", "invalid_size", "empty_color"]


def test_parser_rejects_invalid_rule_type() -> None:
    with pytest.raises(ValueError, match="Unsupported rule type"):
        RuleParser().parse("Test", {"validation_rules": [{"type": "python", "field": "x", "code": "bad", "message": "bad"}]})
