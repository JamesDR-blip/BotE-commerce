from __future__ import annotations

from pathlib import Path

from domain.rule_retriever import RuleQuery
from infrastructure.rules.chroma_rule_retriever import ChromaRuleRetriever
from rule_engine.models import RuleDefinition, RuleSet


def make_rule_sets() -> list[RuleSet]:
    return [
        RuleSet(
            category="Fashion",
            rules=(
                RuleDefinition(
                    type="positive_number",
                    field="price",
                    code="invalid_price",
                    message="Price must be a positive number",
                ),
            ),
            raw={
                "rules": [
                    "Remove extra whitespace from Color.",
                ],
            },
        ),
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


def test_sync_stores_rule_version_and_removes_stale_rules(
    tmp_path: Path,
) -> None:
    retriever = ChromaRuleRetriever(
        path=tmp_path / "chroma",
    )

    initial = make_rule_sets()
    assert retriever.sync_rule_sets(
        initial,
        rule_version="version-one",
    ) == 3

    collection = retriever._collection
    assert collection.count() == 3

    updated = [
        RuleSet(
            category="Fashion",
            rules=(
                RuleDefinition(
                    type="positive_number",
                    field="price",
                    code="invalid_price",
                    message="Price must be a positive number",
                ),
            ),
        ),
    ]

    assert retriever.sync_rule_sets(
        updated,
        rule_version="version-two",
    ) == 1

    assert collection.count() == 1

    stored = collection.get(
        ids=["fashion.executable.invalid_price.0"],
        include=["metadatas"],
    )

    assert stored["ids"] == ["fashion.executable.invalid_price.0"]
    assert stored["metadatas"][0]["rule_version"] == "version-two"

    remaining = collection.get(
        include=["metadatas"],
    )

    assert remaining["ids"] == [
        "fashion.executable.invalid_price.0"
    ]
    assert all(
        metadata["category"] == "Fashion"
        for metadata in remaining["metadatas"]
    )


def test_sync_with_empty_rule_sets_clears_existing_index(
    tmp_path: Path,
) -> None:
    retriever = ChromaRuleRetriever(
        path=tmp_path / "chroma",
    )

    assert retriever.sync_rule_sets(
        make_rule_sets(),
        rule_version="version-one",
    ) == 3

    assert retriever.sync_rule_sets(
        [],
        rule_version="version-two",
    ) == 0

    assert retriever._collection.count() == 0
