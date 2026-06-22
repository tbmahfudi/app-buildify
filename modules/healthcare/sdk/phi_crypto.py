"""
Healthcare SDK — PHI encryption helpers using AES-256 via Fernet (cryptography lib).

T-HC-005  CRITICAL

Fernet provides:
    - AES-128-CBC encryption (uses a 256-bit key internally split into signing + encryption)
    - HMAC-SHA256 authentication
    - Timestamp for TTL support (not used here — PHI has no expiry)

Key management:
    - PHI_ENCRYPTION_KEY env var must be set to a base64-encoded 32-byte key.
    - If not set, a RuntimeError is raised at *import time* (fail-fast).
    - Use generate_phi_key() to generate a new key for initial setup.

Column usage::

    from modules.healthcare.sdk.phi_crypto import EncryptedPHIType

    class PatientProfile(Base):
        national_id = Column(EncryptedPHIType)   # transparent encrypt/decrypt
"""
from __future__ import annotations

import base64
import os
from typing import Any, Optional

# Fail-fast: raise at module import if the library is missing
try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError as _exc:
    raise ImportError(
        "The 'cryptography' package is required for PHI encryption. "
        "Install it with: pip install cryptography"
    ) from _exc

from sqlalchemy import String
from sqlalchemy.types import TypeDecorator


def _load_key() -> bytes:
    """
    Load PHI_ENCRYPTION_KEY from environment and return a Fernet-ready 32-byte key.

    Fernet expects a URL-safe base64-encoded 32-byte key.
    We accept either:
      - A raw 32-byte key already base64-encoded (produced by generate_phi_key())
      - A standard base64-encoded 32-byte value

    Raises RuntimeError at import time if the env var is absent.
    """
    raw = os.environ.get("PHI_ENCRYPTION_KEY", "")
    if not raw:
        raise RuntimeError(
            "PHI_ENCRYPTION_KEY environment variable is not set. "
            "PHI encryption requires this key to be configured. "
            "Generate a key with: from modules.healthcare.sdk.phi_crypto import generate_phi_key; print(generate_phi_key())"
        )
    # Ensure the key is URL-safe base64-encoded bytes (Fernet requirement)
    try:
        # If the caller passed a raw base64 string, normalise to bytes
        key_bytes = raw.encode("ascii") if isinstance(raw, str) else raw
        # Validate it's a proper Fernet key (32 bytes decoded)
        decoded = base64.urlsafe_b64decode(key_bytes + b"==")  # padding tolerance
        if len(decoded) != 32:
            raise ValueError(f"Decoded key length is {len(decoded)}, expected 32 bytes")
        return key_bytes
    except Exception as exc:
        raise RuntimeError(
            f"PHI_ENCRYPTION_KEY is not a valid base64-encoded 32-byte key: {exc}"
        ) from exc


# Module-level Fernet instance — loaded once at import time
_FERNET = Fernet(_load_key())


def generate_phi_key() -> str:
    """
    Generate a new Fernet key suitable for PHI_ENCRYPTION_KEY.

    This is an ops utility — call it once during initial setup and store the
    result in your secrets manager.

    Returns:
        URL-safe base64-encoded 32-byte key as a str.
    """
    return Fernet.generate_key().decode("ascii")


def encrypt_phi(value: str) -> str:
    """
    Encrypt a PHI string value.

    Returns a URL-safe base64-encoded Fernet token (str).
    """
    return _FERNET.encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_phi(value: str) -> str:
    """
    Decrypt a PHI string value produced by encrypt_phi.

    Raises:
        cryptography.fernet.InvalidToken: if the ciphertext is tampered or corrupt.
    """
    return _FERNET.decrypt(value.encode("ascii")).decode("utf-8")


class EncryptedPHIType(TypeDecorator):
    """
    SQLAlchemy TypeDecorator — transparently encrypts on write, decrypts on read.

    Column usage::

        class PatientProfile(Base):
            national_id = Column(EncryptedPHIType)

    The underlying column type is String (stores the Fernet token).
    NULL values pass through unchanged.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Optional[Any], dialect: Any) -> Optional[str]:
        """Called before INSERT/UPDATE — encrypt the plaintext value."""
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
        return encrypt_phi(value)

    def process_result_value(self, value: Optional[Any], dialect: Any) -> Optional[str]:
        """Called after SELECT — decrypt the stored ciphertext."""
        if value is None:
            return None
        try:
            return decrypt_phi(str(value))
        except InvalidToken:
            # Log and return sentinel — do not raise inside ORM result processing
            import logging
            logging.getLogger(__name__).error(
                "PHI decryption failed for a column value — data may be corrupt or "
                "the encryption key has changed."
            )
            return None


__all__ = [
    "EncryptedPHIType",
    "generate_phi_key",
    "encrypt_phi",
    "decrypt_phi",
]
