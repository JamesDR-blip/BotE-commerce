"""Versioned YAML rule repository with mtime-based hot reload."""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
from threading import RLock
from typing import Any
import yaml


class RuleRepository:
    def __init__(self, path: Path) -> None:
        self._path, self._mtime, self._rules, self._version, self._lock = path, -1, {}, "", RLock()
    def get(self, category: str) -> tuple[dict[str, Any], str]:
        with self._lock:
            mtime = self._path.stat().st_mtime_ns
            if mtime != self._mtime:
                raw = self._path.read_bytes(); data = yaml.safe_load(raw) or {}
                if not isinstance(data, dict): raise ValueError("Rules YAML must be a mapping")
                self._rules, self._version, self._mtime = data, sha256(raw).hexdigest()[:12], mtime
            if category not in self._rules: raise KeyError(f"No rules for category '{category}'")
            return self._rules[category], self._version
