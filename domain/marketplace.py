"""Domain contracts for the marketplace and extensibility ecosystem.

This module is framework independent. Marketplace manifests describe verified
package metadata; they do not perform package loading, installation, import,
or cryptographic verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Mapping


_SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


def _required_string(field_name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value


class MarketplacePackageType(str, Enum):
    """Supported marketplace package categories."""

    RULE_PACK = "rule_pack"
    VALIDATOR_PLUGIN = "validator_plugin"
    CHANNEL_CONNECTOR = "channel_connector"


@dataclass(frozen=True)
class RulePackManifest:
    """Declarative metadata describing a marketplace rule pack."""

    package_id: str
    version: str
    publisher: str
    interface_version: str
    category: str
    rules_path: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("package_id", self.package_id),
            ("version", self.version),
            ("publisher", self.publisher),
            ("interface_version", self.interface_version),
            ("category", self.category),
            ("rules_path", self.rules_path),
        ):
            _required_string(field_name, value)

        normalized_path = self.rules_path.replace("\\", "/")
        if normalized_path.startswith("/"):
            raise ValueError("rules_path must be a relative package path")

        if ".." in normalized_path.split("/"):
            raise ValueError("rules_path must not contain parent traversal")


@dataclass(frozen=True)
class PluginManifest:
    """Metadata describing an executable validator or connector plugin."""

    package_id: str
    version: str
    publisher: str
    interface_version: str
    entrypoint: str
    artifact_path: str
    dependencies: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name, value in (
            ("package_id", self.package_id),
            ("version", self.version),
            ("publisher", self.publisher),
            ("interface_version", self.interface_version),
            ("entrypoint", self.entrypoint),
            ("artifact_path", self.artifact_path),
        ):
            _required_string(field_name, value)

        normalized_path = self.artifact_path.replace("\\", "/")
        if normalized_path.startswith("/"):
            raise ValueError("artifact_path must be a relative package path")

        if ".." in normalized_path.split("/"):
            raise ValueError(
                "artifact_path must not contain parent traversal"
            )

        if ":" not in self.entrypoint:
            raise ValueError(
                "entrypoint must use '<module>:<attribute>' format"
            )


@dataclass(frozen=True)
class MarketplacePackage:
    """Verified marketplace package metadata.

    Verification itself is performed outside the domain. This object captures
    the package identity and the manifest required by application/infrastructure
    boundaries after validation.
    """

    package_id: str
    version: str
    package_type: MarketplacePackageType
    publisher: str
    interface_version: str
    content_hash: str
    manifest: Mapping[str, object]
    signature: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("package_id", self.package_id),
            ("version", self.version),
            ("publisher", self.publisher),
            ("interface_version", self.interface_version),
            ("content_hash", self.content_hash),
            ("signature", self.signature),
        ):
            _required_string(field_name, value)

        if not _SHA256_PATTERN.fullmatch(self.content_hash):
            raise ValueError("content_hash must be a SHA-256 hexadecimal digest")

        if not isinstance(self.manifest, Mapping):
            raise ValueError("manifest must be a mapping")


__all__ = [
    "MarketplacePackage",
    "MarketplacePackageType",
    "PluginManifest",
    "RulePackManifest",
]
