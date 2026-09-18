"""API tests for marketplace package installation."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import zipfile

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from api.dependencies import get_current_user
from api.main import create_app
from configs.settings import Settings
from domain.identity import CurrentUser


def _signed_rule_pack() -> tuple[bytes, str, str, str]:
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
  description: Community Fashion rules
  validation_rules:
    - type: required_column
      field: price
      code: missing_column
      message: "Missing required column: price"
"""

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("rules/fashion.yaml", rules)

    payload = buffer.getvalue()
    signature = private_key.sign(payload)
    public_key_bytes = public_key.public_bytes_raw()

    return (
        payload,
        base64.b64encode(public_key_bytes).decode("ascii"),
        base64.b64encode(signature).decode("ascii"),
        hashlib.sha256(payload).hexdigest(),
    )


def _client(tmp_path):
    app = create_app(
        Settings(
            database_url="sqlite://",
            marketplace_staging_path=tmp_path / "marketplace",
        )
    )
    app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="owner-1")
    )
    return app, TestClient(app)


def test_install_signed_rule_pack_endpoint(tmp_path):
    app, client = _client(tmp_path)
    payload, public_key, signature, content_hash = _signed_rule_pack()

    response = client.post(
        "/marketplace/install",
        files={
            "archive": (
                "fashion.zip",
                payload,
                "application/zip",
            )
        },
        data={
            "public_key": public_key,
            "signature": signature,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "package_id": "community.fashion",
        "version": "1.0.0",
        "package_type": "rule_pack",
        "publisher": "community",
        "interface_version": "1",
        "content_hash": content_hash,
    }

    staging_path = (
        tmp_path
        / "marketplace"
        / "community.fashion"
        / "1.0.0"
    )
    assert staging_path.is_dir()
    assert (staging_path / "manifest.json").is_file()
    assert (staging_path / "rules" / "fashion.yaml").is_file()

    assert "staging_path" not in response.json()
    assert "signature" not in response.json()
    assert "public_key" not in response.json()

    assert not any(
        path.name.startswith("marketplace-upload-")
        for path in (tmp_path / "marketplace").iterdir()
    )


def test_install_requires_authentication(tmp_path):
    app = create_app(
        Settings(
            database_url="sqlite://",
            marketplace_staging_path=tmp_path / "marketplace",
        )
    )
    client = TestClient(app)

    payload, public_key, signature, _ = _signed_rule_pack()

    response = client.post(
        "/marketplace/install",
        files={
            "archive": (
                "fashion.zip",
                payload,
                "application/zip",
            )
        },
        data={
            "public_key": public_key,
            "signature": signature,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_install_rejects_invalid_base64(tmp_path):
    _, client = _client(tmp_path)
    payload, _, _, _ = _signed_rule_pack()

    response = client.post(
        "/marketplace/install",
        files={
            "archive": (
                "fashion.zip",
                payload,
                "application/zip",
            )
        },
        data={
            "public_key": "not-base64!",
            "signature": "also-not-base64!",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Invalid Base64 public key or signature"
    )


def test_install_rejects_empty_archive(tmp_path):
    _, client = _client(tmp_path)

    response = client.post(
        "/marketplace/install",
        files={
            "archive": (
                "empty.zip",
                b"",
                "application/zip",
            )
        },
        data={
            "public_key": base64.b64encode(b"key").decode("ascii"),
            "signature": base64.b64encode(b"signature").decode("ascii"),
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Marketplace archive is empty"


def test_install_rejects_unsupported_archive_format(tmp_path):
    _, client = _client(tmp_path)
    payload, public_key, signature, _ = _signed_rule_pack()

    response = client.post(
        "/marketplace/install",
        files={
            "archive": (
                "fashion.exe",
                payload,
                "application/octet-stream",
            )
        },
        data={
            "public_key": public_key,
            "signature": signature,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Unsupported marketplace archive format"
    )


def test_install_rejects_tampered_archive(tmp_path):
    _, client = _client(tmp_path)
    payload, public_key, signature, _ = _signed_rule_pack()

    tampered = bytearray(payload)
    tampered[-1] ^= 0x01

    response = client.post(
        "/marketplace/install",
        files={
            "archive": (
                "fashion.zip",
                bytes(tampered),
                "application/zip",
            )
        },
        data={
            "public_key": public_key,
            "signature": signature,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "marketplace package signature verification failed"
    )


def test_install_rejects_upload_above_configured_limit(tmp_path):
    app = create_app(
        Settings(
            database_url="sqlite://",
            marketplace_staging_path=tmp_path / "marketplace",
            max_upload_bytes=32,
        )
    )
    app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(user_id="owner-1")
    )
    client = TestClient(app)

    payload, public_key, signature, _ = _signed_rule_pack()

    assert len(payload) > 32

    response = client.post(
        "/marketplace/install",
        files={
            "archive": (
                "fashion.zip",
                payload,
                "application/zip",
            )
        },
        data={
            "public_key": public_key,
            "signature": signature,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Marketplace archive exceeds maximum upload size"
    )


def test_marketplace_install_route_is_registered(tmp_path):
    app, _ = _client(tmp_path)

    openapi = app.openapi()

    assert "/marketplace/install" in openapi["paths"]
    assert "post" in openapi["paths"]["/marketplace/install"]

def test_list_marketplace_packages_returns_installed_packages(tmp_path):
    app, client = _client(tmp_path)

    payload, public_key, signature, content_hash = _signed_rule_pack()

    install_response = client.post(
        "/marketplace/install",
        files={
            "archive": (
                "fashion.zip",
                payload,
                "application/zip",
            )
        },
        data={
            "public_key": public_key,
            "signature": signature,
        },
    )

    assert install_response.status_code == 200

    response = client.get("/marketplace/packages")

    assert response.status_code == 200
    assert response.json() == [
        {
            "package_id": "community.fashion",
            "version": "1.0.0",
            "package_type": "rule_pack",
            "publisher": "community",
            "interface_version": "1",
            "content_hash": content_hash,
        }
    ]

    assert "signature" not in response.json()[0]
    assert "staging_path" not in response.json()[0]


def test_list_marketplace_packages_supports_query(tmp_path):
    app, client = _client(tmp_path)

    payload, public_key, signature, _ = _signed_rule_pack()

    response = client.post(
        "/marketplace/install",
        files={
            "archive": (
                "fashion.zip",
                payload,
                "application/zip",
            )
        },
        data={
            "public_key": public_key,
            "signature": signature,
        },
    )

    assert response.status_code == 200

    assert client.get(
        "/marketplace/packages",
        params={"query": "FASHION"},
    ).json()[0]["package_id"] == "community.fashion"

    assert client.get(
        "/marketplace/packages",
        params={"query": "does-not-exist"},
    ).json() == []


def test_list_marketplace_packages_returns_empty_catalog(tmp_path):
    app, client = _client(tmp_path)

    response = client.get("/marketplace/packages")

    assert response.status_code == 200
    assert response.json() == []


def test_list_marketplace_packages_requires_authentication(tmp_path):
    app = create_app(
        Settings(
            database_url="sqlite://",
            marketplace_staging_path=tmp_path / "marketplace",
        )
    )
    client = TestClient(app)

    response = client.get("/marketplace/packages")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_marketplace_packages_route_is_registered(tmp_path):
    app, _ = _client(tmp_path)

    openapi = app.openapi()

    assert "/marketplace/packages" in openapi["paths"]
    assert "get" in openapi["paths"]["/marketplace/packages"]

