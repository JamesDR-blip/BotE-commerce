"""Application port for protecting channel credentials."""
from __future__ import annotations

from typing import Protocol


class CredentialCipher(Protocol):
    """Port for encrypting and decrypting persisted channel credentials."""

    def encrypt(self, plaintext: str) -> str:
        """Return encrypted-at-rest representation of plaintext."""
        ...

    def decrypt(self, ciphertext: str) -> str:
        """Return plaintext credential for controlled in-memory use."""
        ...
