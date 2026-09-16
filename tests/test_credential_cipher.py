from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from application.channels.credential_cipher import CredentialCipher
from configs.settings import Settings
from infrastructure.security.credential_cipher import FernetCredentialCipher


def test_fernet_cipher_satisfies_application_port() -> None:
    cipher: CredentialCipher = FernetCredentialCipher(
        Fernet.generate_key().decode("utf-8")
    )

    assert cipher.encrypt("shop-secret")


def test_fernet_cipher_round_trip() -> None:
    cipher = FernetCredentialCipher(
        Fernet.generate_key().decode("utf-8")
    )

    ciphertext = cipher.encrypt("shop-secret")

    assert ciphertext != "shop-secret"
    assert cipher.decrypt(ciphertext) == "shop-secret"


def test_fernet_cipher_rejects_empty_plaintext() -> None:
    cipher = FernetCredentialCipher(
        Fernet.generate_key().decode("utf-8")
    )

    with pytest.raises(ValueError, match="plaintext is required"):
        cipher.encrypt("")


def test_fernet_cipher_rejects_empty_ciphertext() -> None:
    cipher = FernetCredentialCipher(
        Fernet.generate_key().decode("utf-8")
    )

    with pytest.raises(ValueError, match="ciphertext is required"):
        cipher.decrypt("")


def test_fernet_cipher_rejects_wrong_key() -> None:
    first = FernetCredentialCipher(
        Fernet.generate_key().decode("utf-8")
    )
    second = FernetCredentialCipher(
        Fernet.generate_key().decode("utf-8")
    )

    ciphertext = first.encrypt("shop-secret")

    with pytest.raises(ValueError, match="invalid credential ciphertext"):
        second.decrypt(ciphertext)


def test_fernet_cipher_rejects_invalid_key() -> None:
    with pytest.raises(ValueError, match="invalid credential encryption key"):
        FernetCredentialCipher("not-a-fernet-key")


def test_non_production_can_omit_channel_credential_encryption_key() -> None:
    settings = Settings(
        environment="test",
        database_url="sqlite:///:memory:",
    )

    assert settings.channel_credentials_encryption_key is None

