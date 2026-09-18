from __future__ import annotations

import pytest

from domain.marketplace import (
    MarketplacePackage,
    MarketplacePackageType,
    PluginManifest,
    RulePackManifest,
)


def test_rule_pack_manifest_requires_declarative_rule_artifact() -> None:
    manifest = RulePackManifest(
        package_id="fashion.rules",
        version="1.0.0",
        publisher="example",
        interface_version="1",
        category="Fashion",
        rules_path="rules/fashion.yaml",
    )

    assert manifest.category == "Fashion"
    assert manifest.rules_path == "rules/fashion.yaml"


@pytest.mark.parametrize(
    "rules_path",
    ["/rules.yaml", "\\rules.yaml", "../rules.yaml", "rules/../rules.yaml"],
)
def test_rule_pack_manifest_rejects_unsafe_paths(rules_path: str) -> None:
    with pytest.raises(ValueError):
        RulePackManifest(
            package_id="fashion.rules",
            version="1.0.0",
            publisher="example",
            interface_version="1",
            category="Fashion",
            rules_path=rules_path,
        )


def test_plugin_manifest_requires_module_attribute_entrypoint() -> None:
    manifest = PluginManifest(
        package_id="fashion.validator",
        version="1.0.0",
        publisher="example",
        interface_version="1",
        entrypoint="plugin.module:Validator",
        artifact_path="plugin/module.py",
    )

    assert manifest.entrypoint == "plugin.module:Validator"


def test_plugin_manifest_rejects_invalid_entrypoint() -> None:
    with pytest.raises(ValueError, match="entrypoint"):
        PluginManifest(
            package_id="fashion.validator",
            version="1.0.0",
            publisher="example",
            interface_version="1",
            entrypoint="plugin.module.Validator",
            artifact_path="plugin/module.py",
        )


def test_marketplace_package_requires_sha256_content_hash() -> None:
    package = MarketplacePackage(
        package_id="fashion.rules",
        version="1.0.0",
        package_type=MarketplacePackageType.RULE_PACK,
        publisher="example",
        interface_version="1",
        content_hash="a" * 64,
        manifest={"category": "Fashion"},
        signature="signed-value",
    )

    assert package.package_type is MarketplacePackageType.RULE_PACK


@pytest.mark.parametrize(
    "content_hash",
    ["", "abc", "g" * 64, "a" * 63],
)
def test_marketplace_package_rejects_invalid_content_hash(
    content_hash: str,
) -> None:
    with pytest.raises(ValueError):
        MarketplacePackage(
            package_id="fashion.rules",
            version="1.0.0",
            package_type=MarketplacePackageType.RULE_PACK,
            publisher="example",
            interface_version="1",
            content_hash=content_hash,
            manifest={},
            signature="signed-value",
        )


def test_marketplace_package_is_immutable() -> None:
    package = MarketplacePackage(
        package_id="fashion.rules",
        version="1.0.0",
        package_type=MarketplacePackageType.RULE_PACK,
        publisher="example",
        interface_version="1",
        content_hash="a" * 64,
        manifest={},
        signature="signed-value",
    )

    with pytest.raises(AttributeError):
        package.version = "2.0.0"  # type: ignore[misc]
