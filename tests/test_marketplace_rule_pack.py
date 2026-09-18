from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from infrastructure.marketplace.installer import PackageInstaller
from infrastructure.marketplace.rule_pack import (
    MarketplaceRulePackLoader,
    RulePackLoadError,
)


def _create_signed_rule_pack(
    tmp_path: Path,
    *,
    rules: bytes,
    manifest: dict[str, object] | None = None,
):
    manifest = manifest or {
        "package_id": "fashion-rules",
        "version": "1.0.0",
        "package_type": "rule_pack",
        "publisher": "test-publisher",
        "interface_version": "1",
        "category": "Fashion",
        "rules_path": "rules/fashion.yaml",
    }

    archive_path = tmp_path / "package.zip"

    with ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(manifest).encode("utf-8"),
        )

        rules_path = manifest.get("rules_path")
        if isinstance(rules_path, str) and rules_path.strip():
            archive.writestr(
                rules_path,
                rules,
            )

        artifact_path = manifest.get("artifact_path")
        if isinstance(artifact_path, str) and artifact_path.strip():
            archive.writestr(
                artifact_path,
                b"class Validator:\n    pass\n",
            )

    payload = archive_path.read_bytes()
    private_key = Ed25519PrivateKey.generate()

    installed = PackageInstaller(
        staging_root=tmp_path / "staging",
    ).install(
        archive_path=archive_path,
        public_key=private_key.public_key().public_bytes_raw(),
        signature=private_key.sign(payload),
    )

    return installed


def test_loader_parses_signed_rule_pack_with_existing_rule_parser(
    tmp_path: Path,
) -> None:
    installed = _create_signed_rule_pack(
        tmp_path,
        rules=b"""
Fashion:
  validation_rules:
    - type: required_column
      field: price
      code: missing_column
      message: "Missing required column: price"
    - type: positive_number
      field: price
      code: invalid_price
      message: "Price must be positive"
""",
    )

    rules = MarketplaceRulePackLoader().load(installed)

    assert isinstance(rules.rules, tuple)
    assert [rule.type for rule in rules.rules] == [
        "required_column",
        "positive_number",
    ]
    assert rules.category == "Fashion"


def test_loader_rejects_invalid_rule_type(
    tmp_path: Path,
) -> None:
    installed = _create_signed_rule_pack(
        tmp_path,
        rules=b"""
Fashion:
  validation_rules:
    - type: python
      field: price
      code: unsafe
      message: "unsafe"
""",
    )

    with pytest.raises(
        RulePackLoadError,
        match="validation rules are invalid",
    ):
        MarketplaceRulePackLoader().load(installed)


def test_loader_rejects_missing_category(
    tmp_path: Path,
) -> None:
    installed = _create_signed_rule_pack(
        tmp_path,
        rules=b"""
Cosmetics:
  validation_rules: []
""",
    )

    with pytest.raises(
        RulePackLoadError,
        match="category is missing",
    ):
        MarketplaceRulePackLoader().load(installed)


def test_loader_rejects_invalid_yaml(
    tmp_path: Path,
) -> None:
    installed = _create_signed_rule_pack(
        tmp_path,
        rules=b"""
Fashion:
  validation_rules:
    - [invalid
""",
    )

    with pytest.raises(
        RulePackLoadError,
        match="YAML is invalid",
    ):
        MarketplaceRulePackLoader().load(installed)


def test_loader_does_not_modify_builtin_rules_library(
    tmp_path: Path,
) -> None:
    built_in = Path("rules_library.yaml").read_bytes()

    installed = _create_signed_rule_pack(
        tmp_path,
        rules=b"""
Fashion:
  validation_rules:
    - type: required_column
      field: sku
      code: missing_sku
      message: "Missing required column: sku"
""",
    )

    rules = MarketplaceRulePackLoader().load(installed)

    assert rules.rules[0].field == "sku"
    assert Path("rules_library.yaml").read_bytes() == built_in


def test_loader_rejects_non_rule_pack(
    tmp_path: Path,
) -> None:
    manifest = {
        "package_id": "validator",
        "version": "1.0.0",
        "package_type": "validator_plugin",
        "publisher": "test-publisher",
        "interface_version": "1",
        "entrypoint": "example:Validator",
        "artifact_path": "plugin.py",
        "dependencies": [],
    }

    installed = _create_signed_rule_pack(
        tmp_path,
        manifest=manifest,
        rules=b"Fashion:\n  validation_rules: []\n",
    )


    with pytest.raises(
        RulePackLoadError,
        match="not a RulePack",
    ):
        MarketplaceRulePackLoader().load(installed)



