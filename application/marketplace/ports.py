"""Application contracts for the marketplace and extensibility ecosystem."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from domain.marketplace import MarketplacePackage
from rule_engine.models import RuleSet


class InstalledMarketplacePackage(Protocol):
    """Application-facing handle for a verified staged marketplace package."""

    @property
    def package(self) -> MarketplacePackage:
        ...

    @property
    def staging_path(self) -> Path:
        ...


class MarketplacePackageInstaller(Protocol):
    """Install and verify marketplace packages."""

    def install(
        self,
        *,
        archive_path: Path,
        public_key: bytes,
        signature: bytes,
    ) -> InstalledMarketplacePackage:
        ...



class MarketplacePackageCatalog(Protocol):
    """Read and remove verified packages from marketplace staging."""

    def list_packages(
        self,
        *,
        query: str | None = None,
    ) -> list[MarketplacePackage]:
        ...

    def get_package(
        self,
        *,
        package_id: str,
        version: str,
    ) -> MarketplacePackage | None:
        ...

    def uninstall(
        self,
        *,
        package_id: str,
        version: str,
    ) -> MarketplacePackage:
        ...

class MarketplaceRulePackLoader(Protocol):
    """Load a verified declarative RulePack."""

    def load(
        self,
        installed: InstalledMarketplacePackage,
    ) -> RuleSet:
        ...


__all__ = [
    "InstalledMarketplacePackage",
    "MarketplacePackageCatalog",
    "MarketplacePackageInstaller",
    "MarketplaceRulePackLoader",
]

