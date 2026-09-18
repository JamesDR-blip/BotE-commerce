from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from application.marketplace.marketplace_service import MarketplaceService
from infrastructure.marketplace.installer import PackageInstaller
from infrastructure.marketplace.catalog import MarketplacePackageCatalog
from infrastructure.marketplace.rule_pack import MarketplaceRulePackLoader
from rule_engine.validator import RuleValidator


def _create_signed_rule_pack(tmp_path: Path) -> tuple[Path, bytes, bytes]:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    manifest = {
        "package_id": "community.fashion",
        "version": "1.0.0",
        "package_type": "rule_pack",
        "publisher": "community",
        "interface_version": "1",
        "category": "Fashion",
        "rules_path": "rules/fashion.yaml",
    }

    rules = """
Fashion:
  description: Marketplace Fashion rules
  validation_rules:
    - type: required_column
      field: price
      code: missing_column
      message: "Missing required column: price"
    - type: positive_number
      field: price
      code: invalid_price
      message: "Price must be positive"
"""

    archive_path = tmp_path / "fashion.zip"

    import json

    with ZipFile(archive_path, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("rules/fashion.yaml", rules)

    payload = archive_path.read_bytes()
    signature = private_key.sign(payload)

    return archive_path, public_key.public_bytes_raw(), signature


def _service(tmp_path: Path) -> MarketplaceService:
    return MarketplaceService(
        installer=PackageInstaller(
            staging_root=tmp_path / "staging",
        ),
        catalog=MarketplacePackageCatalog(
            root=tmp_path / "staging",
        ),
        rule_pack_loader=MarketplaceRulePackLoader(),
    )



def _create_signed_rule_pack_version(
    tmp_path: Path,
    version: str,
) -> tuple[Path, bytes, bytes]:
    private_key = Ed25519PrivateKey.generate()
    manifest = {
        "package_id": "community.fashion",
        "version": version,
        "package_type": "rule_pack",
        "publisher": "community",
        "interface_version": "1",
        "category": "Fashion",
        "rules_path": "rules/fashion.yaml",
    }

    rules = """
Fashion:
  description: Marketplace Fashion rules
  validation_rules:
    - type: required_column
      field: price
      code: missing_column
      message: "Missing required column: price"
"""

    archive_path = tmp_path / f"fashion-{version}.zip"

    import json

    with ZipFile(archive_path, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("rules/fashion.yaml", rules)

    payload = archive_path.read_bytes()

    return (
        archive_path,
        private_key.public_key().public_bytes_raw(),
        private_key.sign(payload),
    )

def test_install_and_load_rule_pack_through_application_service(
    tmp_path: Path,
) -> None:
    archive_path, public_key, signature = _create_signed_rule_pack(tmp_path)

    service = _service(tmp_path)

    installed = service.install(
        archive_path=archive_path,
        public_key=public_key,
        signature=signature,
    )

    assert installed.package.package_id == "community.fashion"
    assert installed.package.version == "1.0.0"
    assert installed.staging_path.is_dir()

    rules = service.load_rule_pack(installed)

    assert rules.category == "Fashion"
    assert len(rules.rules) == 2


def test_loaded_rule_pack_uses_existing_deterministic_validator(
    tmp_path: Path,
) -> None:
    archive_path, public_key, signature = _create_signed_rule_pack(tmp_path)

    service = _service(tmp_path)
    installed = service.install(
        archive_path=archive_path,
        public_key=public_key,
        signature=signature,
    )
    rules = service.load_rule_pack(installed)

    frame = pd.DataFrame(
        {
            "price": [-10, 25],
        }
    )

    issues = RuleValidator().validate(frame, rules)

    assert len(issues) == 1
    assert issues[0].code == "invalid_price"


def test_rule_pack_loading_rejects_non_rule_package(
    tmp_path: Path,
) -> None:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    manifest = {
        "package_id": "community.validator",
        "version": "1.0.0",
        "package_type": "validator_plugin",
        "publisher": "community",
        "interface_version": "1",
        "entrypoint": "plugin:Validator",
        "artifact_path": "plugin.py",
        "dependencies": [],
    }

    archive_path = tmp_path / "validator.zip"

    import json

    with ZipFile(archive_path, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr(
            "plugin.py",
            "class Validator:\n    pass\n",
        )

    payload = archive_path.read_bytes()
    signature = private_key.sign(payload)

    service = _service(tmp_path)

    installed = service.install(
        archive_path=archive_path,
        public_key=public_key.public_bytes_raw(),
        signature=signature,
    )

    with pytest.raises(ValueError, match="not a RulePack"):
        service.load_rule_pack(installed)

def test_install_delegates_to_installer(tmp_path: Path) -> None:
    class FakeInstaller:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def install(
            self,
            *,
            archive_path: Path,
            public_key: bytes,
            signature: bytes,
        ):
            self.calls.append(
                {
                    "archive_path": archive_path,
                    "public_key": public_key,
                    "signature": signature,
                }
            )
            return object()

    installer = FakeInstaller()
    service = MarketplaceService(
        installer=installer,  # type: ignore[arg-type]
        catalog=MarketplacePackageCatalog(root=tmp_path / "staging"),
        rule_pack_loader=MarketplaceRulePackLoader(),
    )

    archive_path = tmp_path / "package.zip"
    public_key = b"public-key"
    signature = b"signature"

    result = service.install(
        archive_path=archive_path,
        public_key=public_key,
        signature=signature,
    )

    assert result is not None
    assert installer.calls == [
        {
            "archive_path": archive_path,
            "public_key": public_key,
            "signature": signature,
        }
    ]

def test_update_installs_new_verified_package_version(
    tmp_path: Path,
) -> None:
    archive_path, public_key, signature = _create_signed_rule_pack(tmp_path)

    service = _service(tmp_path)

    installed = service.update(
        archive_path=archive_path,
        public_key=public_key,
        signature=signature,
    )

    assert installed.package.package_id == "community.fashion"
    assert installed.package.version == "1.0.0"
    assert installed.staging_path.is_dir()

    packages = service.list_packages()

    assert [
        (package.package_id, package.version)
        for package in packages
    ] == [
        ("community.fashion", "1.0.0"),
    ]

def test_update_retains_existing_package_versions(
    tmp_path: Path,
) -> None:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes_raw()

    def create_archive(version: str) -> tuple[Path, bytes]:
        manifest = {
            "package_id": "community.fashion",
            "version": version,
            "package_type": "rule_pack",
            "publisher": "community",
            "interface_version": "1",
            "category": "Fashion",
            "rules_path": "rules/fashion.yaml",
        }

        archive_path = tmp_path / f"fashion-{version}.zip"

        import json

        with ZipFile(archive_path, "w") as archive:
            archive.writestr("manifest.json", json.dumps(manifest))
            archive.writestr(
                "rules/fashion.yaml",
                "Fashion:\n  validation_rules: []\n",
            )

        payload = archive_path.read_bytes()
        return archive_path, private_key.sign(payload)

    first_archive, first_signature = create_archive("1.0.0")
    second_archive, second_signature = create_archive("1.1.0")

    service = _service(tmp_path)

    first = service.install(
        archive_path=first_archive,
        public_key=public_key,
        signature=first_signature,
    )
    second = service.update(
        archive_path=second_archive,
        public_key=public_key,
        signature=second_signature,
    )

    assert first.staging_path.is_dir()
    assert second.staging_path.is_dir()
    assert first.staging_path != second.staging_path

    packages = service.list_packages()

    assert [
        (package.package_id, package.version)
        for package in packages
    ] == [
        ("community.fashion", "1.0.0"),
        ("community.fashion", "1.1.0"),
    ]

