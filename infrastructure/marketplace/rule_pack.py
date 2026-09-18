"""Infrastructure loader for verified declarative marketplace RulePacks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from domain.marketplace import MarketplacePackageType
from rule_engine.models import RuleSet
from rule_engine.parser import RuleParser

from infrastructure.marketplace.installer import (
    InstalledMarketplacePackage,
)


class RulePackLoadError(ValueError):
    """Raised when a verified RulePack cannot be loaded safely."""


class MarketplaceRulePackLoader:
    """Load declarative rules from an already verified marketplace package."""

    def __init__(self, parser: RuleParser | None = None) -> None:
        self._parser = parser or RuleParser()

    def load(
        self,
        installed: InstalledMarketplacePackage,
    ) -> RuleSet:
        package = installed.package

        if package.package_type is not MarketplacePackageType.RULE_PACK:
            raise RulePackLoadError(
                "marketplace package is not a RulePack"
            )

        category = self._required_manifest_string(
            package.manifest,
            "category",
        )
        rules_path = self._required_manifest_string(
            package.manifest,
            "rules_path",
        )

        package_root = installed.staging_path.resolve()
        rules_file = self._safe_path(package_root, rules_path)

        if not rules_file.is_file():
            raise RulePackLoadError(
                "RulePack rules file is missing"
            )

        try:
            raw = rules_file.read_bytes()
        except OSError as exc:
            raise RulePackLoadError(
                "unable to read RulePack rules file"
            ) from exc

        try:
            document = yaml.safe_load(raw) or {}
        except yaml.YAMLError as exc:
            raise RulePackLoadError(
                "RulePack YAML is invalid"
            ) from exc

        if not isinstance(document, dict):
            raise RulePackLoadError(
                "RulePack YAML must be a mapping"
            )

        if category not in document:
            raise RulePackLoadError(
                f"RulePack category is missing from YAML: {category}"
            )

        payload = document[category]
        if not isinstance(payload, dict):
            raise RulePackLoadError(
                f"RulePack category must map to a mapping: {category}"
            )

        try:
            return self._parser.parse(category, payload)
        except ValueError as exc:
            raise RulePackLoadError(
                "RulePack validation rules are invalid"
            ) from exc

    @staticmethod
    def _required_manifest_string(
        manifest: dict[str, object] | Any,
        field_name: str,
    ) -> str:
        value = manifest.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise RulePackLoadError(
                f"RulePack manifest field is required: {field_name}"
            )
        return value

    @staticmethod
    def _safe_path(
        package_root: Path,
        relative_path: str,
    ) -> Path:
        normalized = relative_path.replace("\\", "/")
        candidate = (
            package_root
            / Path(*normalized.split("/"))
        ).resolve()

        try:
            candidate.relative_to(package_root)
        except ValueError as exc:
            raise RulePackLoadError(
                "RulePack rules path escapes package staging directory"
            ) from exc

        return candidate


__all__ = [
    "MarketplaceRulePackLoader",
    "RulePackLoadError",
]
