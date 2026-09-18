"""Filesystem-backed catalog for installed marketplace packages."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from domain.marketplace import (
    MarketplacePackage,
    MarketplacePackageType,
    PluginManifest,
    RulePackManifest,
)


class MarketplaceCatalogError(ValueError):
    """Raised when installed marketplace state is invalid."""


class MarketplacePackageCatalog:
    """Discover and remove verified packages from marketplace staging.

    The catalog never imports or executes package artifacts. It trusts only
    installer-owned metadata plus the staged manifest and validates the
    resulting domain object before returning it.
    """

    METADATA_NAME = ".marketplace_metadata.json"
    MANIFEST_NAME = "manifest.json"

    def __init__(self, *, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def list_packages(
        self,
        *,
        query: str | None = None,
    ) -> list[MarketplacePackage]:
        packages: list[MarketplacePackage] = []

        if not self._root.is_dir():
            return packages

        normalized_query = query.strip().casefold() if query else None

        for package_dir in sorted(
            (path for path in self._root.iterdir() if path.is_dir()),
            key=lambda path: path.name.casefold(),
        ):
            for version_dir in sorted(
                (
                    path
                    for path in package_dir.iterdir()
                    if path.is_dir()
                ),
                key=lambda path: path.name.casefold(),
            ):
                package = self._read_package(
                    package_dir.name,
                    version_dir.name,
                    version_dir,
                )

                if normalized_query is None or self._matches(
                    package,
                    normalized_query,
                ):
                    packages.append(package)

        return packages

    def get_package(
        self,
        *,
        package_id: str,
        version: str,
    ) -> MarketplacePackage | None:
        package_root = self._safe_package_path(
            package_id=package_id,
            version=version,
        )

        if not package_root.is_dir():
            return None

        return self._read_package(
            package_id,
            version,
            package_root,
        )

    def uninstall(
        self,
        *,
        package_id: str,
        version: str,
    ) -> MarketplacePackage:
        package_root = self._safe_package_path(
            package_id=package_id,
            version=version,
        )

        if not package_root.is_dir():
            raise FileNotFoundError(
                f"marketplace package not found: {package_id}@{version}"
            )

        package = self._read_package(
            package_id,
            version,
            package_root,
        )

        shutil.rmtree(package_root)

        parent = package_root.parent
        if parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()

        return package

    def _read_package(
        self,
        package_id: str,
        version: str,
        package_root: Path,
    ) -> MarketplacePackage:
        metadata_path = package_root / self.METADATA_NAME
        manifest_path = package_root / self.MANIFEST_NAME

        if not metadata_path.is_file():
            raise MarketplaceCatalogError(
                "installed marketplace package metadata is missing"
            )

        if not manifest_path.is_file():
            raise MarketplaceCatalogError(
                "installed marketplace package manifest is missing"
            )

        try:
            metadata = json.loads(
                metadata_path.read_text(encoding="utf-8")
            )
            manifest = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise MarketplaceCatalogError(
                "installed marketplace metadata is invalid"
            ) from exc

        if not isinstance(metadata, dict) or not isinstance(manifest, dict):
            raise MarketplaceCatalogError(
                "installed marketplace metadata must be JSON objects"
            )

        stored_manifest = metadata.get("manifest")
        if stored_manifest != manifest:
            raise MarketplaceCatalogError(
                "installed marketplace manifest does not match verified metadata"
            )

        self._require_string(metadata, "package_id")
        self._require_string(metadata, "version")
        self._require_string(metadata, "package_type")
        self._require_string(metadata, "publisher")
        self._require_string(metadata, "interface_version")
        self._require_string(metadata, "content_hash")
        self._require_string(metadata, "signature")

        if metadata["package_id"] != package_id:
            raise MarketplaceCatalogError(
                "installed marketplace package ID does not match its path"
            )

        if metadata["version"] != version:
            raise MarketplaceCatalogError(
                "installed marketplace version does not match its path"
            )

        try:
            package_type = MarketplacePackageType(metadata["package_type"])
        except ValueError as exc:
            raise MarketplaceCatalogError(
                "installed marketplace package type is invalid"
            ) from exc

        if not isinstance(stored_manifest, dict):
            raise MarketplaceCatalogError(
                "installed marketplace manifest is invalid"
            )

        self._validate_manifest(
            package_type=package_type,
            manifest=stored_manifest,
        )

        try:
            return MarketplacePackage(
                package_id=metadata["package_id"],
                version=metadata["version"],
                package_type=package_type,
                publisher=metadata["publisher"],
                interface_version=metadata["interface_version"],
                content_hash=metadata["content_hash"],
                manifest=stored_manifest,
                signature=metadata["signature"],
            )
        except (TypeError, ValueError) as exc:
            raise MarketplaceCatalogError(
                "installed marketplace metadata is invalid"
            ) from exc

    @staticmethod
    def _require_string(
        metadata: dict[str, Any],
        field_name: str,
    ) -> str:
        value = metadata.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise MarketplaceCatalogError(
                f"installed marketplace metadata field is invalid: {field_name}"
            )
        return value

    @staticmethod
    def _validate_manifest(
        *,
        package_type: MarketplacePackageType,
        manifest: dict[str, object],
    ) -> None:
        try:
            package_id = manifest["package_id"]
            version = manifest["version"]
            publisher = manifest["publisher"]
            interface_version = manifest["interface_version"]

            if not all(
                isinstance(value, str) and value.strip()
                for value in (
                    package_id,
                    version,
                    publisher,
                    interface_version,
                )
            ):
                raise ValueError("invalid common manifest fields")

            if package_type is MarketplacePackageType.RULE_PACK:
                RulePackManifest(
                    package_id=package_id,
                    version=version,
                    publisher=publisher,
                    interface_version=interface_version,
                    category=manifest["category"],
                    rules_path=manifest["rules_path"],
                )
                return

            dependencies = manifest.get("dependencies", [])
            if not isinstance(dependencies, list):
                raise ValueError("dependencies must be a list")

            PluginManifest(
                package_id=package_id,
                version=version,
                publisher=publisher,
                interface_version=interface_version,
                entrypoint=manifest["entrypoint"],
                artifact_path=manifest["artifact_path"],
                dependencies=tuple(dependencies),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise MarketplaceCatalogError(
                "installed marketplace manifest is invalid"
            ) from exc

    @staticmethod
    def _matches(
        package: MarketplacePackage,
        query: str,
    ) -> bool:
        values = [
            package.package_id,
            package.publisher,
            package.package_type.value,
            package.interface_version,
        ]

        category = package.manifest.get("category")
        if isinstance(category, str):
            values.append(category)

        return any(query in value.casefold() for value in values)

    def _safe_package_path(
        self,
        *,
        package_id: str,
        version: str,
    ) -> Path:
        for value in (package_id, version):
            candidate = Path(value)

            if (
                not value.strip()
                or candidate.is_absolute()
                or ".." in candidate.parts
            ):
                raise MarketplaceCatalogError(
                    "invalid marketplace package path"
                )

        target = (self._root / package_id / version).resolve()

        try:
            target.relative_to(self._root)
        except ValueError as exc:
            raise MarketplaceCatalogError(
                "invalid marketplace package path"
            ) from exc

        return target


__all__ = [
    "MarketplaceCatalogError",
    "MarketplacePackageCatalog",
]
