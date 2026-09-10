from __future__ import annotations

import pytest

from application.rules.rule_intelligence_service import (
    RuleIntelligenceService,
)
from domain.rule_retriever import (
    RetrievedRuleMatch,
    RuleQuery,
    SemanticRulePack,
)


class FakeRuleRetriever:
    def __init__(self, result: SemanticRulePack) -> None:
        self.result = result
        self.calls: list[RuleQuery] = []

    def search(self, query: RuleQuery) -> SemanticRulePack:
        self.calls.append(query)
        return self.result


def make_pack() -> SemanticRulePack:
    query = RuleQuery(
        query="price validation",
        category="Fashion",
        fields=("price",),
        top_k=3,
    )

    return SemanticRulePack(
        query=query,
        matches=(
            RetrievedRuleMatch(
                rule_id="price-positive",
                content="Price must be positive",
                score=0.95,
                category="Fashion",
            ),
            RetrievedRuleMatch(
                rule_id="price-required",
                content="Price is required",
                score=0.80,
                category="Fashion",
            ),
            RetrievedRuleMatch(
                rule_id="price-format",
                content="Price must be numeric",
                score=0.60,
                category="Fashion",
            ),
        ),
    )


def test_search_delegates_to_retriever() -> None:
    pack = make_pack()
    retriever = FakeRuleRetriever(pack)
    service = RuleIntelligenceService(retriever=retriever)

    result = service.search(query=pack.query)

    assert result == pack
    assert retriever.calls == [pack.query]


def test_recommend_filters_matches_by_min_score() -> None:
    pack = make_pack()
    retriever = FakeRuleRetriever(pack)
    service = RuleIntelligenceService(retriever=retriever)

    result = service.recommend(
        query=pack.query,
        min_score=0.80,
    )

    assert [match.rule_id for match in result.matches] == [
        "price-positive",
        "price-required",
    ]
    assert result.query == pack.query
    assert retriever.calls == [pack.query]


def test_recommend_keeps_all_matches_with_zero_threshold() -> None:
    pack = make_pack()
    service = RuleIntelligenceService(
        retriever=FakeRuleRetriever(pack),
    )

    result = service.recommend(
        query=pack.query,
        min_score=0.0,
    )

    assert len(result.matches) == 3


def test_recommend_rejects_invalid_threshold() -> None:
    pack = make_pack()
    service = RuleIntelligenceService(
        retriever=FakeRuleRetriever(pack),
    )

    with pytest.raises(
        ValueError,
        match="min_score must be between 0 and 1",
    ):
        service.recommend(
            query=pack.query,
            min_score=1.1,
        )
