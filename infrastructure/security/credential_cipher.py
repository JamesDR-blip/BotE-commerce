"""Infrastructure implementation for encrypted channel credentials."""
from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


class FernetCredentialCipher:
    """Encrypt channel credentials with a configured Fernet key."""

    def __init__(self, key: str) -> None:
        if not key.strip():
            raise ValueError("credential encryption key is required")

        try:
            self._fernet = Fernet(key.encode("utf-8"))
        except (ValueError, TypeError) as exc:
            raise ValueError("invalid credential encryption key") from exc

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            raise ValueError("credential plaintext is required")

        return self._fernet.encrypt(
            plaintext.encode("utf-8")
        ).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            raise ValueError("credential ciphertext is required")

        try:
            return self._fernet.decrypt(
                ciphertext.encode("utf-8")
            ).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("invalid credential ciphertext") from exc
