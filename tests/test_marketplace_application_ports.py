from __future__ import annotations

from pathlib import Path

import pytest

from application.marketplace.marketplace_service import MarketplaceService
from application.marketplace.ports import InstalledMarketplacePackage
from domain.marketplace import MarketplacePackage, MarketplacePackageType
from rule_engine.models import RuleSet


class FakeInstalledPackage:
    def __init__(self, package: MarketplacePackage) -> None:
        self.package = package
        self.staging_path = Path("staging")


class FakeInstaller:
    def __init__(self, result: InstalledMarketplacePackage) -> None:
        self.result = result
        self.calls: list[dict[str, object]] = []

    def install(
        self,
        *,
        archive_path: Path,
        public_key: bytes,
        signature: bytes,
    ) -> InstalledMarketplacePackage:
        self.calls.append(
            {
                "archive_path": archive_path,
                "public_key": public_key,
                "signature": signature,
            }
        )
        return self.result


class FakeCatalog:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def list_packages(self, *, query: str | None = None):
        self.calls.append({"operation": "list", "query": query})
        return []

    def get_package(self, *, package_id: str, version: str):
        self.calls.append(
            {
                "operation": "get",
                "package_id": package_id,
                "version": version,
            }
        )
        return None

    def uninstall(self, *, package_id: str, version: str):
        self.calls.append(
            {
                "operation": "uninstall",
                "package_id": package_id,
                "version": version,
            }
        )
        raise FileNotFoundError("not found")


class FakeRulePackLoader:
    def __init__(self, result: RuleSet) -> None:
        self.result = result
        self.calls: list[InstalledMarketplacePackage] = []

    def load(self, installed: InstalledMarketplacePackage) -> RuleSet:
        self.calls.append(installed)
        return self.result


def _package(package_type: MarketplacePackageType) -> MarketplacePackage:
    return MarketplacePackage(
        package_id="community.test",
        version="1.0.0",
        package_type=package_type,
        publisher="community",
        interface_version="1",
        content_hash="a" * 64,
        manifest={},
        signature="signature",
    )


def test_application_service_install_uses_installer_port() -> None:
    installed = FakeInstalledPackage(
        _package(MarketplacePackageType.RULE_PACK)
    )
    installer = FakeInstaller(installed)
    loader = FakeRulePackLoader(
        RuleSet(category="Fashion", rules=(), raw={})
    )
    catalog = FakeCatalog()
    service = MarketplaceService(
        installer=installer,
        catalog=catalog,
        rule_pack_loader=loader,
    )

    archive_path = Path("package.zip")
    public_key = b"public-key"
    signature = b"signature"

    result = service.install(
        archive_path=archive_path,
        public_key=public_key,
        signature=signature,
    )

    assert result is installed
    assert installer.calls == [
        {
            "archive_path": archive_path,
            "public_key": public_key,
            "signature": signature,
        }
    ]


def test_application_service_load_rule_pack_uses_loader_port() -> None:
    installed = FakeInstalledPackage(
        _package(MarketplacePackageType.RULE_PACK)
    )
    expected = RuleSet(category="Fashion", rules=(), raw={})
    installer = FakeInstaller(installed)
    loader = FakeRulePackLoader(expected)

    catalog = FakeCatalog()
    service = MarketplaceService(
        installer=installer,
        catalog=catalog,
        rule_pack_loader=loader,
    )

    result = service.load_rule_pack(installed)

    assert result is expected
    assert loader.calls == [installed]


def test_application_service_rejects_non_rule_package() -> None:
    installed = FakeInstalledPackage(
        _package(MarketplacePackageType.VALIDATOR_PLUGIN)
    )
    installer = FakeInstaller(installed)
    loader = FakeRulePackLoader(
        RuleSet(category="unused", rules=(), raw={})
    )
    catalog = FakeCatalog()
    service = MarketplaceService(
        installer=installer,
        catalog=catalog,
        rule_pack_loader=loader,
    )

    with pytest.raises(ValueError, match="not a RulePack"):
        service.load_rule_pack(installed)

    assert loader.calls == []
