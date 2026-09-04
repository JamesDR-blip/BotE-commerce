"""Rule retrieval agent for category-specific declarative rules."""
from __future__ import annotations

from typing import Protocol

from rule_engine.models import RuleSet


class RuleProvider(Protocol):
    def get(self, category: str) -> tuple[RuleSet, str]:
        ...


class RuleRetrieverAgent:
    def __init__(self, provider: RuleProvider) -> None:
        self._provider = provider

    def retrieve(self, category: str) -> tuple[RuleSet, str]:
        return self._provider.get(category)