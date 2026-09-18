"""Application service for governed marketplace package installation."""

from __future__ import annotations

from pathlib import Path

from domain.marketplace import MarketplacePackage, MarketplacePackageType
from rule_engine.models import RuleSet

from application.marketplace.ports import (
    InstalledMarketplacePackage,
    MarketplacePackageCatalog,
    MarketplacePackageInstaller,
    MarketplaceRulePackLoader,
)


class MarketplaceService:
    """Orchestrate verified marketplace installation without executing code."""

    def __init__(
        self,
        *,
        installer: MarketplacePackageInstaller,
        catalog: MarketplacePackageCatalog,
        rule_pack_loader: MarketplaceRulePackLoader,
    ) -> None:
        self._installer = installer
        self._catalog = catalog
        self._rule_pack_loader = rule_pack_loader

    def install(
        self,
        *,
        archive_path: Path,
        public_key: bytes,
        signature: bytes,
    ) -> InstalledMarketplacePackage:
        """Verify and stage a marketplace package."""
        return self._installer.install(
            archive_path=archive_path,
            public_key=public_key,
            signature=signature,
        )

    def update(
        self,
        *,
        archive_path: Path,
        public_key: bytes,
        signature: bytes,
    ) -> InstalledMarketplacePackage:
        """Install a verified new package version without removing existing versions."""
        return self._installer.install(
            archive_path=archive_path,
            public_key=public_key,
            signature=signature,
        )

    def list_packages(
        self,
        *,
        query: str | None = None,
    ) -> list[MarketplacePackage]:
        """List locally installed marketplace packages."""
        return self._catalog.list_packages(query=query)

    def get_package(
        self,
        *,
        package_id: str,
        version: str,
    ) -> MarketplacePackage | None:
        """Return one locally installed package, if present."""
        return self._catalog.get_package(
            package_id=package_id,
            version=version,
        )

    def uninstall(
        self,
        *,
        package_id: str,
        version: str,
    ) -> MarketplacePackage:
        """Remove one installed package version."""
        return self._catalog.uninstall(
            package_id=package_id,
            version=version,
        )
    def load_rule_pack(
        self,
        installed: InstalledMarketplacePackage,
    ) -> RuleSet:
        """Load a verified RulePack through the existing rule parser."""
        if (
            installed.package.package_type
            is not MarketplacePackageType.RULE_PACK
        ):
            raise ValueError("marketplace package is not a RulePack")

        return self._rule_pack_loader.load(installed)


__all__ = ["MarketplaceService"]


