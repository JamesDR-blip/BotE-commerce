from __future__ import annotations

from pathlib import Path
from tarfile import FIFOTYPE, LNKTYPE, SYMTYPE, TarFile, TarInfo
from zipfile import ZipFile

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from infrastructure.marketplace.archive import (
    ArchiveInspector,
    ArchiveSecurityError,
)
from infrastructure.marketplace.signature import (
    Ed25519PackageSignatureVerifier,
    PackageSignatureError,
)


def test_archive_inspector_rejects_unsafe_member_paths() -> None:
    for member_name in (
        "/absolute/file.txt",
        r"\absolute\file.txt",
        "../outside.txt",
        r"..\outside.txt",
        "safe/../../outside.txt",
        r"safe\..\outside.txt",
        r"C:\outside.txt",
    ):
        with pytest.raises(ArchiveSecurityError):
            ArchiveInspector.validate_member_path(member_name)


def test_archive_inspector_accepts_relative_member_paths() -> None:
    assert (
        ArchiveInspector.validate_member_path("rules/fashion.yaml")
        == "rules/fashion.yaml"
    )


def test_archive_inspector_lists_zip_without_extracting(tmp_path: Path) -> None:
    archive_path = tmp_path / "package.zip"

    with ZipFile(archive_path, "w") as archive:
        archive.writestr("manifest.json", b"{}")
        archive.writestr("rules/fashion.yaml", b"rules: []")

    assert ArchiveInspector().list_zip_members(str(archive_path)) == (
        "manifest.json",
        "rules/fashion.yaml",
    )


def test_archive_inspector_rejects_unsafe_zip_member(tmp_path: Path) -> None:
    archive_path = tmp_path / "package.zip"

    with ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.txt", b"malicious")

    with pytest.raises(ArchiveSecurityError):
        ArchiveInspector().list_zip_members(str(archive_path))


def test_archive_inspector_lists_tar_without_extracting(tmp_path: Path) -> None:
    archive_path = tmp_path / "package.tar"

    with TarFile.open(archive_path, "w") as archive:
        source = tmp_path / "rules.yaml"
        source.write_bytes(b"rules: []")
        archive.add(source, arcname="rules/fashion.yaml")

    assert ArchiveInspector().list_tar_members(str(archive_path)) == (
        "rules/fashion.yaml",
    )


@pytest.mark.parametrize(
    "member_type",
    ["symlink", "hardlink", "fifo"],
)
def test_archive_inspector_rejects_unsafe_tar_member_types(
    tmp_path: Path,
    member_type: str,
) -> None:
    archive_path = tmp_path / f"package-{member_type}.tar"

    with TarFile.open(archive_path, "w") as archive:
        member = TarInfo(f"unsafe/{member_type}")

        if member_type == "symlink":
            member.type = SYMTYPE
            member.linkname = "../../outside.txt"
        elif member_type == "hardlink":
            member.type = LNKTYPE
            member.linkname = "../../outside.txt"
        else:
            member.type = FIFOTYPE

        archive.addfile(member)

    with pytest.raises(ArchiveSecurityError):
        ArchiveInspector().list_tar_members(str(archive_path))


def test_ed25519_verifier_accepts_valid_signature() -> None:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    payload = b"canonical marketplace package payload"
    signature = private_key.sign(payload)

    Ed25519PackageSignatureVerifier().verify(
        public_key=public_key.public_bytes_raw(),
        payload=payload,
        signature=signature,
    )


def test_ed25519_verifier_rejects_tampered_payload() -> None:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    payload = b"canonical marketplace package payload"
    signature = private_key.sign(payload)

    with pytest.raises(PackageSignatureError):
        Ed25519PackageSignatureVerifier().verify(
            public_key=public_key.public_bytes_raw(),
            payload=payload + b"tampered",
            signature=signature,
        )


def test_ed25519_verifier_rejects_invalid_signature() -> None:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    with pytest.raises(PackageSignatureError):
        Ed25519PackageSignatureVerifier().verify(
            public_key=public_key.public_bytes_raw(),
            payload=b"payload",
            signature=b"invalid",
        )

