from pathlib import Path

from repositories.rules import RuleRepository


def test_rule_repository_all_returns_all_rule_sets_and_version() -> None:
    repository = RuleRepository(Path("rules_library.yaml"))

    rule_sets, version = repository.all()

    assert rule_sets
    assert version
    assert all(rule_set.category for rule_set in rule_sets)
