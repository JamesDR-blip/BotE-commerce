"""Rule retrieval agent for category-specific declarative rules."""
from __future__ import annotations

from repositories.rules import RuleRepository
from rule_engine.models import RuleSet


class RuleRetrieverAgent:
    def __init__(self, repository: RuleRepository) -> None:
        self._repository = repository

    def retrieve(self, category: str) -> tuple[RuleSet, str]:
        return self._repository.get(category)
