from __future__ import annotations

from pathlib import Path

from domain.rule_retriever import RuleQuery
from infrastructure.rules.chroma_rule_retriever import ChromaRuleRetriever
from rule_engine.models import RuleDefinition, RuleSet


def make_rule_set() -> RuleSet:
    return RuleSet(
        category="Fashion",
        rules=(
            RuleDefinition(
                type="positive_number",
                field="price",
                code="invalid_price",
                message="Price must be a positive number",
            ),
            RuleDefinition(
                type="enum",
                field="size",
                code="invalid_size",
                message="Size must be S, M, L, XL or XXL",
                values=("S", "M", "L", "XL", "XXL"),
            ),
        ),
        raw={
            "rules": [
                "Remove extra whitespace from Color.",
            ],
        },
    )


def test_chroma_retriever_indexes_and_searches_rules(tmp_path: Path) -> None:
    retriever = ChromaRuleRetriever(
        path=tmp_path / "chroma",
    )

    indexed = retriever.index_rule_sets([make_rule_set()])

    assert indexed == 3

    result = retriever.search(
        RuleQuery(
            query="price should be positive numeric",
            category="Fashion",
            top_k=2,
        )
    )

    assert len(result.matches) == 2
    assert result.matches[0].category == "Fashion"
    assert result.matches[0].score >= result.matches[1].score
    assert result.matches[0].metadata["category"] == "Fashion"


def test_chroma_retriever_supports_category_filter(tmp_path: Path) -> None:
    retriever = ChromaRuleRetriever(
        path=tmp_path / "chroma",
    )

    retriever.index_rule_sets(
        [
            make_rule_set(),
            RuleSet(
                category="Cosmetics",
                rules=(
                    RuleDefinition(
                        type="non_empty",
                        field="ingredients",
                        code="empty_ingredients",
                        message="Ingredients cannot be empty",
                    ),
                ),
            ),
        ]
    )

    result = retriever.search(
        RuleQuery(
            query="ingredients cannot be empty",
            category="Cosmetics",
            top_k=5,
        )
    )

    assert result.matches
    assert all(
        match.category == "Cosmetics"
        for match in result.matches
    )


def test_descriptive_rules_are_marked_non_executable(
    tmp_path: Path,
) -> None:
    retriever = ChromaRuleRetriever(
        path=tmp_path / "chroma",
    )

    retriever.index_rule_sets([make_rule_set()])

    result = retriever.search(
        RuleQuery(
            query="remove extra whitespace from color",
            category="Fashion",
            top_k=5,
        )
    )

    descriptive = [
        match
        for match in result.matches
        if match.metadata.get("source_kind") == "descriptive"
    ]

    assert descriptive
    assert descriptive[0].metadata["executable"] is False
from pathlib import Path

from infrastructure.rules.chroma_rule_retriever import ChromaRuleRetriever


def test_chroma_retriever_uses_embedded_persistent_client(
    tmp_path: Path,
) -> None:
    retriever = ChromaRuleRetriever(
        path=tmp_path / "chroma",
    )

    assert type(retriever._client).__name__ == "Client"
    assert retriever._client is not None


def test_chroma_retriever_does_not_expose_remote_server_configuration() -> None:
    source = Path(
        "infrastructure/rules/chroma_rule_retriever.py"
    ).read_text(encoding="utf-8")

    assert "chromadb.HttpClient" not in source
    assert "HttpClient(" not in source
    assert "trust_remote_code" not in source
    assert "chroma run" not in source
    assert "chroma-server" not in source
