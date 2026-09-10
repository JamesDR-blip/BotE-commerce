from __future__ import annotations

from application.rules.rule_intelligence_service import (
    RuleIntelligenceService,
)
from domain.rule_retriever import (
    RetrievedRuleMatch,
    RuleQuery,
    SemanticRulePack,
)
from rule_engine.models import RuleDefinition, RuleSet


class SyncingFakeRuleRetriever:
    def __init__(self) -> None:
        self.calls: list[tuple[list[RuleSet], str]] = []

    def sync_rule_sets(
        self,
        rule_sets: list[RuleSet],
        *,
        rule_version: str,
    ) -> int:
        self.calls.append((rule_sets, rule_version))
        return len(rule_sets)

    def search(self, query: RuleQuery) -> SemanticRulePack:
        return SemanticRulePack(
            query=query,
            matches=(
                RetrievedRuleMatch(
                    rule_id="test.rule",
                    content="Test rule",
                    score=1.0,
                ),
            ),
        )


def test_sync_delegates_to_retriever() -> None:
    retriever = SyncingFakeRuleRetriever()
    service = RuleIntelligenceService(retriever=retriever)

    rule_sets = [
        RuleSet(
            category="Fashion",
            rules=(
                RuleDefinition(
                    type="positive_number",
                    field="price",
                    code="invalid_price",
                    message="Price must be positive",
                ),
            ),
        ),
    ]

    result = service.sync(
        rule_sets=rule_sets,
        rule_version="abc123",
    )

    assert result == 1
    assert retriever.calls == [
        (rule_sets, "abc123"),
    ]
