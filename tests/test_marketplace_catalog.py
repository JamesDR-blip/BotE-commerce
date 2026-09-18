from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.marketplace.catalog import (
    MarketplaceCatalogError,
    MarketplacePackageCatalog,
)


def _write_installed_rule_pack(
    root: Path,
    *,
    package_id: str = "community.fashion",
    version: str = "1.0.0",
    publisher: str = "community",
    category: str = "Fashion",
) -> Path:
    package_root = root / package_id / version
    package_root.mkdir(parents=True)

    manifest = {
        "package_id": package_id,
        "version": version,
        "package_type": "rule_pack",
        "publisher": publisher,
        "interface_version": "1",
        "category": category,
        "rules_path": "rules/fashion.yaml",
    }

    metadata = {
        "package_id": package_id,
        "version": version,
        "package_type": "rule_pack",
        "publisher": publisher,
        "interface_version": "1",
        "content_hash": "a" * 64,
        "signature": "bb" * 64,
        "manifest": manifest,
    }

    (package_root / "manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    (package_root / ".marketplace_metadata.json").write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )
    (package_root / "rules").mkdir()
    (package_root / "rules" / "fashion.yaml").write_text(
        "category: Fashion\nrules: []\n",
        encoding="utf-8",
    )

    return package_root


def test_catalog_lists_installed_packages(tmp_path: Path) -> None:
    _write_installed_rule_pack(tmp_path)

    catalog = MarketplacePackageCatalog(root=tmp_path)

    packages = catalog.list_packages()

    assert len(packages) == 1
    package = packages[0]
    assert package.package_id == "community.fashion"
    assert package.version == "1.0.0"
    assert package.publisher == "community"
    assert package.package_type.value == "rule_pack"
    assert package.content_hash == "a" * 64


def test_catalog_query_filters_package_metadata(tmp_path: Path) -> None:
    _write_installed_rule_pack(
        tmp_path,
        package_id="community.fashion",
        category="Fashion",
    )
    _write_installed_rule_pack(
        tmp_path,
        package_id="community.cosmetics",
        version="2.0.0",
        category="Cosmetics",
    )

    catalog = MarketplacePackageCatalog(root=tmp_path)

    assert [
        package.package_id
        for package in catalog.list_packages(query="COSMETICS")
    ] == ["community.cosmetics"]

    assert [
        package.package_id
        for package in catalog.list_packages(query="community")
    ] == [
        "community.cosmetics",
        "community.fashion",
    ]


def test_catalog_get_package_returns_exact_version(tmp_path: Path) -> None:
    _write_installed_rule_pack(tmp_path, version="1.0.0")
    _write_installed_rule_pack(tmp_path, version="2.0.0")

    catalog = MarketplacePackageCatalog(root=tmp_path)

    package = catalog.get_package(
        package_id="community.fashion",
        version="2.0.0",
    )

    assert package is not None
    assert package.version == "2.0.0"


def test_catalog_get_missing_package_returns_none(tmp_path: Path) -> None:
    catalog = MarketplacePackageCatalog(root=tmp_path)

    assert catalog.get_package(
        package_id="community.missing",
        version="1.0.0",
    ) is None


def test_catalog_uninstall_removes_one_version_and_preserves_other_versions(
    tmp_path: Path,
) -> None:
    _write_installed_rule_pack(tmp_path, version="1.0.0")
    _write_installed_rule_pack(tmp_path, version="2.0.0")

    catalog = MarketplacePackageCatalog(root=tmp_path)

    removed = catalog.uninstall(
        package_id="community.fashion",
        version="1.0.0",
    )

    assert removed.version == "1.0.0"
    assert not (tmp_path / "community.fashion" / "1.0.0").exists()
    assert (tmp_path / "community.fashion" / "2.0.0").is_dir()

    remaining = catalog.list_packages()
    assert [(p.package_id, p.version) for p in remaining] == [
        ("community.fashion", "2.0.0"),
    ]


def test_catalog_uninstall_missing_package_raises(tmp_path: Path) -> None:
    catalog = MarketplacePackageCatalog(root=tmp_path)

    with pytest.raises(FileNotFoundError):
        catalog.uninstall(
            package_id="community.missing",
            version="1.0.0",
        )


@pytest.mark.parametrize(
    ("package_id", "version"),
    [
        ("../outside", "1.0.0"),
        ("community.fashion", "../outside"),
        ("C:\\outside", "1.0.0"),
    ],
)
def test_catalog_rejects_unsafe_package_paths(
    tmp_path: Path,
    package_id: str,
    version: str,
) -> None:
    catalog = MarketplacePackageCatalog(root=tmp_path)

    with pytest.raises(MarketplaceCatalogError):
        catalog.get_package(
            package_id=package_id,
            version=version,
        )


def test_catalog_rejects_missing_metadata(tmp_path: Path) -> None:
    package_root = tmp_path / "community.fashion" / "1.0.0"
    package_root.mkdir(parents=True)
    (package_root / "manifest.json").write_text(
        json.dumps(
            {
                "package_id": "community.fashion",
                "version": "1.0.0",
                "package_type": "rule_pack",
                "publisher": "community",
                "interface_version": "1",
                "category": "Fashion",
                "rules_path": "rules/fashion.yaml",
            }
        ),
        encoding="utf-8",
    )

    catalog = MarketplacePackageCatalog(root=tmp_path)

    with pytest.raises(
        MarketplaceCatalogError,
        match="metadata is missing",
    ):
        catalog.list_packages()


def test_catalog_rejects_manifest_metadata_mismatch(tmp_path: Path) -> None:
    package_root = _write_installed_rule_pack(tmp_path)

    manifest = json.loads(
        (package_root / "manifest.json").read_text(encoding="utf-8")
    )
    manifest["category"] = "Cosmetics"

    (package_root / "manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    catalog = MarketplacePackageCatalog(root=tmp_path)

    with pytest.raises(
        MarketplaceCatalogError,
        match="does not match verified metadata",
    ):
        catalog.list_packages()


def test_catalog_rejects_invalid_metadata(tmp_path: Path) -> None:
    package_root = _write_installed_rule_pack(tmp_path)

    metadata = json.loads(
        (package_root / ".marketplace_metadata.json").read_text(
            encoding="utf-8"
        )
    )
    metadata["content_hash"] = "not-a-sha256"

    (package_root / ".marketplace_metadata.json").write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )

    catalog = MarketplacePackageCatalog(root=tmp_path)

    with pytest.raises(
        MarketplaceCatalogError,
        match="installed marketplace metadata is invalid",
    ):
        catalog.list_packages()


def test_catalog_does_not_import_or_execute_package_artifacts(
    tmp_path: Path,
) -> None:
    package_root = _write_installed_rule_pack(tmp_path)

    marker = package_root / "rules" / "malicious.py"
    marker.write_text(
        "raise RuntimeError('package code executed')\n",
        encoding="utf-8",
    )

    catalog = MarketplacePackageCatalog(root=tmp_path)

    packages = catalog.list_packages()

    assert len(packages) == 1
    assert marker.is_file()
