from __future__ import annotations

from pathlib import Path

from domain.rule_retriever import RuleQuery
from infrastructure.rules.chroma_rule_retriever import ChromaRuleRetriever
from repositories.rules import RuleRepository


def build_retriever(tmp_path: Path) -> ChromaRuleRetriever:
    repository = RuleRepository(Path("rules_library.yaml"))
    rule_sets, _ = repository.all()

    retriever = ChromaRuleRetriever(
        path=tmp_path / "chroma",
    )
    indexed = retriever.index_rule_sets(list(rule_sets))

    assert indexed == 16

    return retriever


def test_english_query_retrieves_vietnamese_color_rule(
    tmp_path: Path,
) -> None:
    retriever = build_retriever(tmp_path)

    result = retriever.search(
        RuleQuery(
            query="remove unnecessary whitespace from color field",
            category="Fashion",
            top_k=3,
        )
    )

    assert result.matches
    top_match = result.matches[0]

    assert top_match.rule_id == "fashion.descriptive.1"
    assert top_match.metadata["source_kind"] == "descriptive"
    assert top_match.metadata["executable"] is False
    assert top_match.score >= 0.70


def test_english_query_retrieves_vietnamese_ingredients_rule(
    tmp_path: Path,
) -> None:
    retriever = build_retriever(tmp_path)

    result = retriever.search(
        RuleQuery(
            query="ingredients should not be empty",
            category="Cosmetics",
            top_k=3,
        )
    )

    assert result.matches
    top_match = result.matches[0]

    assert top_match.rule_id == "cosmetics.descriptive.1"
    assert top_match.metadata["source_kind"] == "descriptive"
    assert top_match.metadata["executable"] is False
    assert top_match.score >= 0.70


def test_price_query_retrieves_price_rule_knowledge(
    tmp_path: Path,
) -> None:
    retriever = build_retriever(tmp_path)

    result = retriever.search(
        RuleQuery(
            query="product price must be greater than zero",
            category="Fashion",
            top_k=3,
        )
    )

    assert result.matches
    top_match = result.matches[0]

    assert top_match.rule_id == "fashion.descriptive.2"
    assert top_match.score >= 0.70


def test_semantic_scores_are_bounded(
    tmp_path: Path,
) -> None:
    retriever = build_retriever(tmp_path)

    result = retriever.search(
        RuleQuery(
            query="product price validation",
            category="Fashion",
            top_k=5,
        )
    )

    assert result.matches
    assert all(
        0.0 <= match.score <= 1.0
        for match in result.matches
    )
