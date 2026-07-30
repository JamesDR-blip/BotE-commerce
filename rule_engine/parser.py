"""Parse and validate YAML rule definitions without executing code."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from rule_engine.models import RuleDefinition, RuleSet, RuleType

_RULE_TYPES = {"required_column", "positive_number", "enum", "non_empty", "regex"}


class RuleParser:
    """Convert a category's YAML mapping into a typed rule set."""

    def parse(self, category: str, payload: Mapping[str, Any]) -> RuleSet:
        raw_rules = payload.get("validation_rules", [])
        if raw_rules is None:
            raw_rules = ()
        if not isinstance(raw_rules, list):
            raise ValueError(f"validation_rules for '{category}' must be a list")
        rules = tuple(self._parse_rule(category, item) for item in raw_rules)
        return RuleSet(category=category, rules=rules, raw=dict(payload))

    def _parse_rule(self, category: str, payload: object) -> RuleDefinition:
        if not isinstance(payload, Mapping):
            raise ValueError(f"Each validation rule for '{category}' must be a mapping")
        rule_type = payload.get("type")
        field = payload.get("field")
        code = payload.get("code")
        message = payload.get("message")
        if rule_type not in _RULE_TYPES:
            raise ValueError(f"Unsupported rule type for '{category}': {rule_type!r}")
        if not all(isinstance(value, str) and value for value in (field, code, message)):
            raise ValueError(f"Rule for '{category}' requires non-empty type, field, code, and message")
        values = payload.get("values", [])
        if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            raise ValueError(f"Rule values for '{category}.{field}' must be a list of strings")
        pattern = payload.get("pattern")
        normalization_pattern = payload.get("normalization_pattern")
        issue_field = payload.get("issue_field")
        severity = payload.get("severity", "error")
        if pattern is not None and not isinstance(pattern, str):
            raise ValueError(f"Rule pattern for '{category}.{field}' must be a string")
        if normalization_pattern is not None and not isinstance(normalization_pattern, str):
            raise ValueError(f"Rule normalization_pattern for '{category}.{field}' must be a string")
        if issue_field is not None and not isinstance(issue_field, str):
            raise ValueError(f"Rule issue_field for '{category}.{field}' must be a string")
        if not isinstance(severity, str):
            raise ValueError(f"Rule severity for '{category}.{field}' must be a string")
        if rule_type == "enum" and not values:
            raise ValueError(f"Enum rule for '{category}.{field}' requires values")
        if rule_type == "regex" and not pattern:
            raise ValueError(f"Regex rule for '{category}.{field}' requires a pattern")
        return RuleDefinition(
            type=cast(RuleType, rule_type),
            field=field,
            code=code,
            message=message,
            issue_field=issue_field,
            severity=severity,
            values=tuple(values),
            pattern=pattern,
            normalization_pattern=normalization_pattern,
        )


__all__ = ["RuleParser"]
