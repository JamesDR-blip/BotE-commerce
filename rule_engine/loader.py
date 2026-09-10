"""Versioned YAML rule loading with parser validation and hot reload."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from threading import RLock
from typing import Any

import yaml

from rule_engine.models import RuleSet
from rule_engine.parser import RuleParser


class RuleLoader:
    """Load YAML rules once per file version and return typed category rules."""

    def __init__(self, path: Path, parser: RuleParser | None = None) -> None:
        self._path = path
        self._parser = parser or RuleParser()
        self._mtime = -1
        self._rules: dict[str, RuleSet] = {}
        self._version = ""
        self._lock = RLock()

    def get(self, category: str) -> tuple[RuleSet, str]:
        with self._lock:
            self._ensure_loaded()
            if category not in self._rules:
                raise KeyError(f"No rules for category '{category}'")
            return self._rules[category], self._version

    def all(self) -> tuple[tuple[RuleSet, ...], str]:
        """Return all parsed rule sets and the current source version."""

        with self._lock:
            self._ensure_loaded()
            return tuple(self._rules.values()), self._version

    def _ensure_loaded(self) -> None:
        mtime = self._path.stat().st_mtime_ns
        if mtime != self._mtime:
            self._reload()

    def _reload(self) -> None:
        raw = self._path.read_bytes()
        document = yaml.safe_load(raw) or {}
        if not isinstance(document, dict):
            raise ValueError("Rules YAML must be a mapping")

        rules: dict[str, RuleSet] = {}
        for category, payload in document.items():
            if not isinstance(category, str) or not isinstance(payload, dict):
                raise ValueError(
                    "Each rules YAML category must map to a mapping"
                )
            rules[category] = self._parser.parse(category, payload)

        self._rules = rules
        self._version = sha256(raw).hexdigest()[:12]
        self._mtime = self._path.stat().st_mtime_ns


__all__ = ["RuleLoader"]
