"""Infrastructure implementation for unavailable credential encryption."""
from __future__ import annotations


class UnavailableCredentialCipher:
    """Fail-closed credential cipher used when encryption is not configured."""

    _ERROR = "channel credential encryption key is not configured"

    def encrypt(self, plaintext: str) -> str:
        raise ValueError(self._ERROR)

    def decrypt(self, ciphertext: str) -> str:
        raise ValueError(self._ERROR)
