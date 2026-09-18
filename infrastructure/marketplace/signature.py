"""Infrastructure implementation for marketplace package signatures."""

from __future__ import annotations

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
)


class PackageSignatureError(ValueError):
    """Raised when a marketplace package signature is invalid."""


class Ed25519PackageSignatureVerifier:
    """Verify detached Ed25519 signatures over package payload bytes."""

    def verify(
        self,
        *,
        public_key: bytes,
        payload: bytes,
        signature: bytes,
    ) -> None:
        try:
            key = Ed25519PublicKey.from_public_bytes(public_key)
            key.verify(signature, payload)
        except (ValueError, TypeError, InvalidSignature) as exc:
            raise PackageSignatureError(
                "invalid marketplace package signature"
            ) from exc
