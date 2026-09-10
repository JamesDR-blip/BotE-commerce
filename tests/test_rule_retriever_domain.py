from __future__ import annotations

import pytest

from domain.rule_retriever import (
    RetrievedRuleMatch,
    RuleQuery,
    SemanticRulePack,
)


def test_rule_query_defaults_and_validates() -> None:
    query = RuleQuery(
        query="product price validation",
        category="Fashion",
        fields=("price", "size"),
    )

    assert query.query == "product price validation"
    assert query.category == "Fashion"
    assert query.fields == ("price", "size")
    assert query.top_k == 5


def test_rule_query_rejects_empty_query() -> None:
    with pytest.raises(ValueError, match="query cannot be empty"):
        RuleQuery(query="   ")


def test_rule_query_rejects_invalid_top_k() -> None:
    with pytest.raises(ValueError, match="top_k must be at least 1"):
        RuleQuery(
            query="price validation",
            top_k=0,
        )


def test_rule_query_rejects_duplicate_fields() -> None:
    with pytest.raises(ValueError, match="fields must be unique"):
        RuleQuery(
            query="product schema",
            fields=("price", "price"),
        )


def test_retrieved_rule_match_validates_score() -> None:
    match = RetrievedRuleMatch(
        rule_id="fashion.price.positive",
        content="Price must be a positive number",
        score=0.91,
        category="Fashion",
        metadata={"source": "rules_library.yaml"},
    )

    assert match.rule_id == "fashion.price.positive"
    assert match.content == "Price must be a positive number"
    assert match.score == 0.91
    assert match.category == "Fashion"


@pytest.mark.parametrize("score", [-0.01, 1.01])
def test_retrieved_rule_match_rejects_invalid_score(score: float) -> None:
    with pytest.raises(
        ValueError,
        match="score must be between 0 and 1",
    ):
        RetrievedRuleMatch(
            rule_id="fashion.price.positive",
            content="Price must be a positive number",
            score=score,
        )


def test_semantic_rule_pack_preserves_query_and_matches() -> None:
    query = RuleQuery(
        query="price column should contain positive numeric values",
        category="Fashion",
        fields=("price",),
        top_k=2,
    )

    matches = (
        RetrievedRuleMatch(
            rule_id="fashion.price.positive",
            content="Price must be a positive number",
            score=0.95,
            category="Fashion",
        ),
        RetrievedRuleMatch(
            rule_id="fashion.required.price",
            content="Missing required column: price",
            score=0.89,
            category="Fashion",
        ),
    )

    pack = SemanticRulePack(
        query=query,
        matches=matches,
    )

    assert pack.query == query
    assert pack.matches == matches


def test_semantic_rule_pack_rejects_duplicate_rule_ids() -> None:
    query = RuleQuery(query="price validation")

    match = RetrievedRuleMatch(
        rule_id="fashion.price.positive",
        content="Price must be a positive number",
        score=0.95,
    )

    with pytest.raises(ValueError, match="duplicate rule ids"):
        SemanticRulePack(
            query=query,
            matches=(match, match),
        )
