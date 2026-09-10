"""Chroma-backed semantic rule retrieval infrastructure."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction,
)

from domain.rule_retriever import (
    RetrievedRuleMatch,
    RuleQuery,
    RuleRetriever,
    SemanticRulePack,
)
from rule_engine.models import RuleDefinition, RuleSet


class ChromaRuleRetriever(RuleRetriever):
    """Persistent Chroma implementation of the semantic rule-retrieval port."""

    COLLECTION_NAME = "ecommerce_rules"
    EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(
        self,
        *,
        path: Path,
        collection_name: str = COLLECTION_NAME,
        embedding_model: str = EMBEDDING_MODEL,
    ) -> None:
        self._client = chromadb.PersistentClient(path=str(path))
        self._embedding_function = None
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            configuration={"hnsw": {"space": "cosine"}},
        )
        self._embedding_model = embedding_model

    def _get_embedding_function(
        self,
    ) -> SentenceTransformerEmbeddingFunction:
        if self._embedding_function is None:
            self._embedding_function = SentenceTransformerEmbeddingFunction(
                model_name=self._embedding_model,
                device="cpu",
                normalize_embeddings=True,
            )

        return self._embedding_function

    def _get_embedding_function(
        self,
    ) -> SentenceTransformerEmbeddingFunction:
        if self._embedding_function is None:
            self._embedding_function = SentenceTransformerEmbeddingFunction(
                model_name=self._embedding_model,
                device="cpu",
                normalize_embeddings=True,
            )

        return self._embedding_function

    def _embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return self._get_embedding_function()(texts)

    def index_rule_sets(
        self,
        rule_sets: list[RuleSet],
        *,
        rule_version: str | None = None,
    ) -> int:
        """Upsert declarative and descriptive rule knowledge into Chroma."""

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for rule_set in rule_sets:
            for index, rule in enumerate(rule_set.rules):
                rule_id = self._rule_id(rule_set.category, rule, index)
                ids.append(rule_id)
                documents.append(
                    self._rule_document(rule_set.category, rule)
                )
                metadatas.append(
                    {
                        "category": rule_set.category,
                        "source_kind": "executable",
                        "executable": True,
                        "rule_type": rule.type,
                        "code": rule.code,
                        "field": rule.field,
                        "embedding_model": self._embedding_model,
                        "rule_version": rule_version or "",
                    }
                )

            raw_rules = rule_set.raw.get("rules", ())
            if isinstance(raw_rules, list):
                for index, content in enumerate(raw_rules):
                    if not isinstance(content, str) or not content.strip():
                        continue

                    rule_id = (
                        f"{self._slug(rule_set.category)}"
                        f".descriptive.{index}"
                    )
                    ids.append(rule_id)
                    documents.append(content.strip())
                    metadatas.append(
                        {
                            "category": rule_set.category,
                            "source_kind": "descriptive",
                            "executable": False,
                            "embedding_model": self._embedding_model,
                            "rule_version": rule_version or "",
                        }
                    )

        if not ids:
            return 0

        self._collection.upsert(
            ids=ids,
            embeddings=self._embed(documents),
            documents=documents,
            metadatas=metadatas,
        )
        return len(ids)

    def sync_rule_sets(
        self,
        rule_sets: list[RuleSet],
        *,
        rule_version: str,
    ) -> int:
        """Synchronize the persistent index with the current YAML version."""

        expected_ids: set[str] = set()

        for rule_set in rule_sets:
            for index, rule in enumerate(rule_set.rules):
                expected_ids.add(
                    self._rule_id(rule_set.category, rule, index)
                )

            raw_rules = rule_set.raw.get("rules", ())
            if isinstance(raw_rules, list):
                for index, content in enumerate(raw_rules):
                    if isinstance(content, str) and content.strip():
                        expected_ids.add(
                            f"{self._slug(rule_set.category)}"
                            f".descriptive.{index}"
                        )

        existing = self._collection.get(include=[])
        existing_ids = set(existing.get("ids", []))
        stale_ids = existing_ids - expected_ids

        if stale_ids:
            self._collection.delete(ids=list(stale_ids))

        if not expected_ids:
            return 0

        return self.index_rule_sets(
            rule_sets,
            rule_version=rule_version,
        )


    def search(self, query: RuleQuery) -> SemanticRulePack:
        """Search indexed rule knowledge using semantic similarity."""

        where = (
            {"category": query.category}
            if query.category is not None
            else None
        )

        result = self._collection.query(
            query_embeddings=self._embed([query.query]),
            n_results=query.top_k,
            where=where,
        )

        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        matches = tuple(
            RetrievedRuleMatch(
                rule_id=rule_id,
                content=document,
                score=self._distance_to_score(distance),
                category=self._metadata_category(metadata),
                metadata=metadata or {},
            )
            for rule_id, document, metadata, distance in zip(
                ids,
                documents,
                metadatas,
                distances,
            )
        )

        return SemanticRulePack(
            query=query,
            matches=matches,
        )

    @staticmethod
    def _rule_id(
        category: str,
        rule: RuleDefinition,
        index: int,
    ) -> str:
        return (
            f"{ChromaRuleRetriever._slug(category)}"
            f".executable.{rule.code}.{index}"
        )

    @staticmethod
    def _rule_document(category: str, rule: RuleDefinition) -> str:
        return (
            f"Category: {category}. "
            f"Field: {rule.field}. "
            f"Rule type: {rule.type}. "
            f"{rule.message}"
        )

    @staticmethod
    def _slug(value: str) -> str:
        return (
            value.strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

    @staticmethod
    def _distance_to_score(distance: float) -> float:
        """Convert Chroma cosine distance to a bounded similarity score."""

        return max(0.0, min(1.0, 1.0 - float(distance)))

    @staticmethod
    def _metadata_category(
        metadata: dict[str, Any] | None,
    ) -> str | None:
        if metadata is None:
            return None

        category = metadata.get("category")
        return category if isinstance(category, str) else None


__all__ = ["ChromaRuleRetriever"]
