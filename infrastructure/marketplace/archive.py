"""Infrastructure primitives for safely inspecting marketplace archives."""

from __future__ import annotations

from pathlib import PurePosixPath, PureWindowsPath
from tarfile import TarFile
from zipfile import ZipFile


class ArchiveSecurityError(ValueError):
    """Raised when an archive contains an unsafe member path or type."""


class ArchiveInspector:
    """Inspect archive members without extracting or executing them."""

    @staticmethod
    def validate_member_path(member_name: str) -> str:
        if not isinstance(member_name, str) or not member_name.strip():
            raise ArchiveSecurityError("archive member path is required")

        normalized = member_name.replace("\\", "/")
        posix_path = PurePosixPath(normalized)
        windows_path = PureWindowsPath(member_name)

        if normalized.startswith("/"):
            raise ArchiveSecurityError(
                "archive member path must be relative"
            )

        if windows_path.drive or windows_path.root:
            raise ArchiveSecurityError(
                "archive member path must be relative"
            )

        if any(part == ".." for part in posix_path.parts):
            raise ArchiveSecurityError(
                "archive member path must not contain parent traversal"
            )

        return str(posix_path)

    def list_zip_members(self, archive_path: str) -> tuple[str, ...]:
        with ZipFile(archive_path, "r") as archive:
            return tuple(
                self.validate_member_path(info.filename)
                for info in archive.infolist()
            )

    def list_tar_members(self, archive_path: str) -> tuple[str, ...]:
        with TarFile.open(archive_path, "r:*") as archive:
            members = archive.getmembers()

            for member in members:
                self.validate_member_path(member.name)

                if not member.isdir() and not member.isfile():
                    raise ArchiveSecurityError(
                        "archive contains unsupported TAR member type"
                    )

            return tuple(
                self.validate_member_path(member.name)
                for member in members
            )
