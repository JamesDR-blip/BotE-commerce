"""Infrastructure installer for verified marketplace packages."""

from __future__ import annotations
from dataclasses import dataclass

import hashlib
import json
import shutil
import stat
import tempfile
from pathlib import Path, PurePosixPath
from tarfile import TarFile
from zipfile import ZipFile

from domain.marketplace import (
    MarketplacePackage,
    MarketplacePackageType,
    PluginManifest,
    RulePackManifest,
)
from infrastructure.marketplace.archive import (
    ArchiveInspector,
    ArchiveSecurityError,
)
from infrastructure.marketplace.signature import (
    Ed25519PackageSignatureVerifier,
)


@dataclass(frozen=True)
class InstalledMarketplacePackage:
    """Verified marketplace package together with its isolated staging path."""

    package: MarketplacePackage
    staging_path: Path


class MarketplaceInstallError(ValueError):
    """Raised when a marketplace package cannot be safely installed."""


class PackageInstaller:
    """Verify and stage marketplace packages without executing package code."""

    MANIFEST_NAME = "manifest.json"
    METADATA_NAME = ".marketplace_metadata.json"

    def __init__(
        self,
        *,
        staging_root: Path,
        archive_inspector: ArchiveInspector | None = None,
        signature_verifier: Ed25519PackageSignatureVerifier | None = None,
    ) -> None:
        self._staging_root = staging_root.resolve()
        self._staging_root.mkdir(parents=True, exist_ok=True)
        self._archive_inspector = archive_inspector or ArchiveInspector()
        self._signature_verifier = (
            signature_verifier or Ed25519PackageSignatureVerifier()
        )

    def install(
        self,
        *,
        archive_path: Path,
        public_key: bytes,
        signature: bytes,
    ) -> InstalledMarketplacePackage:
        archive_path = archive_path.resolve()

        if not archive_path.is_file():
            raise MarketplaceInstallError("marketplace archive not found")

        payload = archive_path.read_bytes()

        try:
            self._signature_verifier.verify(
                public_key=public_key,
                payload=payload,
                signature=signature,
            )
        except ValueError as exc:
            raise MarketplaceInstallError(
                "marketplace package signature verification failed"
            ) from exc

        content_hash = hashlib.sha256(payload).hexdigest()

        try:
            manifest = self._read_manifest(archive_path)
            package = self._build_package(
                manifest=manifest,
                content_hash=content_hash,
                signature=signature.hex(),
            )
            self._validate_archive_members(archive_path, manifest)
            staging_path = self._stage_archive(
                archive_path=archive_path,
                package=package,
            )
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise MarketplaceInstallError(
                "marketplace package validation failed"
            ) from exc

        return InstalledMarketplacePackage(
            package=package,
            staging_path=staging_path,
        )

    def _read_manifest(self, archive_path: Path) -> dict[str, object]:
        suffix = archive_path.suffix.lower()

        if suffix == ".zip":
            with ZipFile(archive_path, "r") as archive:
                names = self._archive_inspector.list_zip_members(
                    str(archive_path)
                )
                self._require_manifest(names)
                raw = archive.read(self.MANIFEST_NAME)
        elif suffix in {".tar", ".gz", ".tgz", ".bz2", ".xz"}:
            with TarFile.open(archive_path, "r:*") as archive:
                names = self._archive_inspector.list_tar_members(
                    str(archive_path)
                )
                self._require_manifest(names)
                member = archive.getmember(self.MANIFEST_NAME)
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise MarketplaceInstallError(
                        "manifest.json must be a regular file"
                    )
                raw = extracted.read()
        else:
            raise MarketplaceInstallError(
                "unsupported marketplace archive format"
            )

        document = json.loads(raw)
        if not isinstance(document, dict):
            raise MarketplaceInstallError(
                "manifest.json must contain a JSON object"
            )

        return document

    @staticmethod
    def _require_manifest(names: tuple[str, ...]) -> None:
        normalized = tuple(
            PurePosixPath(name).as_posix()
            for name in names
        )
        if normalized.count(PackageInstaller.MANIFEST_NAME) != 1:
            raise MarketplaceInstallError(
                "archive must contain exactly one manifest.json"
            )

    @staticmethod
    def _required_string(
        manifest: dict[str, object],
        field_name: str,
    ) -> str:
        value = manifest.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise MarketplaceInstallError(
                f"manifest field is required: {field_name}"
            )
        return value

    def _build_package(
        self,
        *,
        manifest: dict[str, object],
        content_hash: str,
        signature: str,
    ) -> MarketplacePackage:
        package_type_raw = self._required_string(
            manifest,
            "package_type",
        )

        try:
            package_type = MarketplacePackageType(package_type_raw)
        except ValueError as exc:
            raise MarketplaceInstallError(
                f"unsupported marketplace package type: {package_type_raw}"
            ) from exc

        package_id = self._required_string(manifest, "package_id")
        version = self._required_string(manifest, "version")
        publisher = self._required_string(manifest, "publisher")
        interface_version = self._required_string(
            manifest,
            "interface_version",
        )

        if package_type is MarketplacePackageType.RULE_PACK:
            RulePackManifest(
                package_id=package_id,
                version=version,
                publisher=publisher,
                interface_version=interface_version,
                category=self._required_string(manifest, "category"),
                rules_path=self._required_string(manifest, "rules_path"),
            )
        else:
            dependencies = manifest.get("dependencies", ())
            if not isinstance(dependencies, list) or not all(
                isinstance(item, str) and item.strip()
                for item in dependencies
            ):
                raise MarketplaceInstallError(
                    "dependencies must be a list of non-empty strings"
                )

            PluginManifest(
                package_id=package_id,
                version=version,
                publisher=publisher,
                interface_version=interface_version,
                entrypoint=self._required_string(
                    manifest,
                    "entrypoint",
                ),
                artifact_path=self._required_string(
                    manifest,
                    "artifact_path",
                ),
                dependencies=tuple(dependencies),
            )

        return MarketplacePackage(
            package_id=package_id,
            version=version,
            package_type=package_type,
            publisher=publisher,
            interface_version=interface_version,
            content_hash=content_hash,
            manifest=manifest,
            signature=signature,
        )

    def _validate_archive_members(
        self,
        archive_path: Path,
        manifest: dict[str, object],
    ) -> None:
        suffix = archive_path.suffix.lower()

        if suffix == ".zip":
            with ZipFile(archive_path, "r") as archive:
                seen: set[str] = set()

                for info in archive.infolist():
                    normalized = self._archive_inspector.validate_member_path(
                        info.filename
                    )

                    if normalized in seen:
                        raise MarketplaceInstallError(
                            "archive contains duplicate member paths"
                        )
                    seen.add(normalized)

                    mode = (
                        (info.external_attr >> 16) & 0xFFFF
                        if info.create_system == 3
                        else 0
                    )
                    if mode and stat.S_ISLNK(mode):
                        raise ArchiveSecurityError(
                            "archive contains unsupported ZIP symlink"
                        )

        elif suffix in {".tar", ".gz", ".tgz", ".bz2", ".xz"}:
            with TarFile.open(archive_path, "r:*") as archive:
                seen: set[str] = set()

                for member in archive.getmembers():
                    normalized = (
                        self._archive_inspector.validate_member_path(
                            member.name
                        )
                    )

                    if normalized in seen:
                        raise MarketplaceInstallError(
                            "archive contains duplicate member paths"
                        )
                    seen.add(normalized)

                    if not member.isdir() and not member.isfile():
                        raise ArchiveSecurityError(
                            "archive contains unsupported TAR member type"
                        )

        else:
            raise MarketplaceInstallError(
                "unsupported marketplace archive format"
            )

        package_type = MarketplacePackageType(
            self._required_string(manifest, "package_type")
        )

        if package_type is MarketplacePackageType.RULE_PACK:
            rules_path = self._required_string(manifest, "rules_path")
            normalized = ArchiveInspector.validate_member_path(rules_path)

            if normalized not in seen:
                raise MarketplaceInstallError(
                    "manifest rules_path is missing from archive"
                )

    def _stage_archive(
        self,
        *,
        archive_path: Path,
        package: MarketplacePackage,
    ) -> Path:
        package_root = (
            self._staging_root
            / package.package_id
            / package.version
        ).resolve()

        try:
            package_root.relative_to(self._staging_root)
        except ValueError as exc:
            raise MarketplaceInstallError(
                "invalid marketplace staging path"
            ) from exc

        if package_root.exists():
            shutil.rmtree(package_root)

        temporary_root = Path(
            tempfile.mkdtemp(
                prefix=".marketplace-",
                dir=str(self._staging_root),
            )
        )

        try:
            self._extract_safely(
                archive_path=archive_path,
                destination=temporary_root,
            )
            self._write_install_metadata(
                destination=temporary_root,
                package=package,
            )
            package_root.parent.mkdir(parents=True, exist_ok=True)
            temporary_root.replace(package_root)
        except Exception:
            shutil.rmtree(temporary_root, ignore_errors=True)
            raise

        return package_root

    def _write_install_metadata(
        self,
        *,
        destination: Path,
        package: MarketplacePackage,
    ) -> None:
        metadata = {
            "package_id": package.package_id,
            "version": package.version,
            "package_type": package.package_type.value,
            "publisher": package.publisher,
            "interface_version": package.interface_version,
            "content_hash": package.content_hash,
            "signature": package.signature,
            "manifest": dict(package.manifest),
        }

        (destination / self.METADATA_NAME).write_text(
            json.dumps(metadata, sort_keys=True),
            encoding="utf-8",
        )
    def _extract_safely(
        self,
        *,
        archive_path: Path,
        destination: Path,
    ) -> None:
        suffix = archive_path.suffix.lower()

        if suffix == ".zip":
            with ZipFile(archive_path, "r") as archive:
                for info in archive.infolist():
                    normalized = (
                        self._archive_inspector.validate_member_path(
                            info.filename
                        )
                    )
                    target = self._safe_target(
                        destination,
                        normalized,
                    )

                    if info.is_dir():
                        target.mkdir(parents=True, exist_ok=True)
                        continue

                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(info, "r") as source:
                        with target.open("xb") as output:
                            shutil.copyfileobj(source, output)

        elif suffix in {".tar", ".gz", ".tgz", ".bz2", ".xz"}:
            with TarFile.open(archive_path, "r:*") as archive:
                for member in archive.getmembers():
                    normalized = (
                        self._archive_inspector.validate_member_path(
                            member.name
                        )
                    )
                    target = self._safe_target(
                        destination,
                        normalized,
                    )

                    if member.isdir():
                        target.mkdir(parents=True, exist_ok=True)
                        continue

                    if not member.isfile():
                        raise ArchiveSecurityError(
                            "archive contains unsupported TAR member type"
                        )

                    target.parent.mkdir(parents=True, exist_ok=True)
                    source = archive.extractfile(member)
                    if source is None:
                        raise MarketplaceInstallError(
                            "unable to read archive member"
                        )

                    with source, target.open("xb") as output:
                        shutil.copyfileobj(source, output)

        else:
            raise MarketplaceInstallError(
                "unsupported marketplace archive format"
            )

    @staticmethod
    def _safe_target(destination: Path, member_name: str) -> Path:
        target = (destination / Path(*PurePosixPath(member_name).parts)).resolve()

        try:
            target.relative_to(destination.resolve())
        except ValueError as exc:
            raise ArchiveSecurityError(
                "archive member escapes staging directory"
            ) from exc

        return target


__all__ = ["InstalledMarketplacePackage", "MarketplaceInstallError", "PackageInstaller"]




