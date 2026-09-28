from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from infrastructure.marketplace.installer import (
    MarketplaceInstallError,
    PackageInstaller,
)


def _create_signed_zip(
    tmp_path: Path,
    *,
    manifest: dict[str, object],
    rules: bytes = b"Fashion:\n  required_columns:\n    - sku\n",
) -> tuple[Path, bytes, bytes]:
    archive_path = tmp_path / "package.zip"

    with ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(manifest).encode("utf-8"),
        )
        rules_path = manifest.get("rules_path")
        if isinstance(rules_path, str) and rules_path.strip():
            archive.writestr(rules_path, rules)

    payload = archive_path.read_bytes()
    private_key = Ed25519PrivateKey.generate()

    return (
        archive_path,
        private_key.public_key().public_bytes_raw(),
        private_key.sign(payload),
    )


def _rule_manifest() -> dict[str, object]:
    return {
        "package_id": "fashion-rules",
        "version": "1.0.0",
        "package_type": "rule_pack",
        "publisher": "test-publisher",
        "interface_version": "1",
        "category": "Fashion",
        "rules_path": "rules/fashion.yaml",
    }


def test_installer_verifies_and_stages_signed_rule_pack(
    tmp_path: Path,
) -> None:
    archive_path, public_key, signature = _create_signed_zip(
        tmp_path,
        manifest=_rule_manifest(),
    )

    installed = PackageInstaller(
        staging_root=tmp_path / "staging",
    ).install(
        archive_path=archive_path,
        public_key=public_key,
        signature=signature,
    )

    package = installed.package
    staging_path = installed.staging_path

    assert package.package_id == "fashion-rules"
    assert package.package_type.value == "rule_pack"
    assert package.content_hash == hashlib.sha256(
        archive_path.read_bytes()
    ).hexdigest()
    assert (staging_path / "manifest.json").is_file()
    assert (staging_path / ".marketplace_metadata.json").is_file()
    assert (staging_path / "rules" / "fashion.yaml").read_bytes()


def test_installer_rejects_tampered_archive(
    tmp_path: Path,
) -> None:
    archive_path, public_key, signature = _create_signed_zip(
        tmp_path,
        manifest=_rule_manifest(),
    )

    archive_path.write_bytes(archive_path.read_bytes() + b"tampered")

    with pytest.raises(MarketplaceInstallError):
        PackageInstaller(
            staging_root=tmp_path / "staging",
        ).install(
            archive_path=archive_path,
            public_key=public_key,
            signature=signature,
        )

    assert not (tmp_path / "staging" / "fashion-rules").exists()


def test_installer_rejects_unsigned_package(
    tmp_path: Path,
) -> None:
    archive_path, public_key, _ = _create_signed_zip(
        tmp_path,
        manifest=_rule_manifest(),
    )

    with pytest.raises(MarketplaceInstallError):
        PackageInstaller(
            staging_root=tmp_path / "staging",
        ).install(
            archive_path=archive_path,
            public_key=public_key,
            signature=b"invalid",
        )

    assert not (tmp_path / "staging" / "fashion-rules").exists()


def test_installer_rejects_invalid_manifest(
    tmp_path: Path,
) -> None:
    manifest = _rule_manifest()
    manifest.pop("rules_path")

    archive_path, public_key, signature = _create_signed_zip(
        tmp_path,
        manifest=manifest,
    )

    with pytest.raises(MarketplaceInstallError):
        PackageInstaller(
            staging_root=tmp_path / "staging",
        ).install(
            archive_path=archive_path,
            public_key=public_key,
            signature=signature,
        )

    assert not (tmp_path / "staging" / "fashion-rules").exists()


def test_installer_rejects_rules_path_missing_from_archive(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "package.zip"
    manifest = _rule_manifest()

    with ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(manifest).encode("utf-8"),
        )

    payload = archive_path.read_bytes()
    private_key = Ed25519PrivateKey.generate()

    with pytest.raises(MarketplaceInstallError):
        PackageInstaller(
            staging_root=tmp_path / "staging",
        ).install(
            archive_path=archive_path,
            public_key=private_key.public_key().public_bytes_raw(),
            signature=private_key.sign(payload),
        )


def test_installer_rejects_duplicate_archive_paths(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "package.zip"
    manifest = _rule_manifest()

    with ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(manifest).encode("utf-8"),
        )
        archive.writestr("rules/fashion.yaml", b"safe")

        with pytest.warns(UserWarning, match=r"Duplicate name: 'rules/fashion\.yaml'"):
            archive.writestr("rules/fashion.yaml", b"duplicate")

    payload = archive_path.read_bytes()
    private_key = Ed25519PrivateKey.generate()

    with pytest.raises(MarketplaceInstallError):
        PackageInstaller(
            staging_root=tmp_path / "staging",
        ).install(
            archive_path=archive_path,
            public_key=private_key.public_key().public_bytes_raw(),
            signature=private_key.sign(payload),
        )


