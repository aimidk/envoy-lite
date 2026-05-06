"""Simple symmetric encryption/decryption for env var values using Fernet."""

from __future__ import annotations

import base64
import os
from typing import Dict

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""


class MissingKeyError(EncryptionError):
    """Raised when no encryption key is available."""


ENV_KEY_VAR = "ENVOY_LITE_SECRET_KEY"


def _get_fernet(key: str | None = None) -> "Fernet":
    if Fernet is None:  # pragma: no cover
        raise EncryptionError(
            "cryptography package is required: pip install cryptography"
        )
    resolved_key = key or os.environ.get(ENV_KEY_VAR)
    if not resolved_key:
        raise MissingKeyError(
            f"No encryption key provided. Set {ENV_KEY_VAR} or pass key= explicitly."
        )
    try:
        return Fernet(resolved_key.encode() if isinstance(resolved_key, str) else resolved_key)
    except Exception as exc:
        raise EncryptionError(f"Invalid Fernet key: {exc}") from exc


def generate_key() -> str:
    """Generate a new URL-safe base64-encoded 32-byte key."""
    if Fernet is None:  # pragma: no cover
        raise EncryptionError("cryptography package is required")
    return Fernet.generate_key().decode()


def encrypt_value(plaintext: str, key: str | None = None) -> str:
    """Encrypt *plaintext* and return a base64-encoded ciphertext string."""
    f = _get_fernet(key)
    try:
        token = f.encrypt(plaintext.encode())
        return token.decode()
    except Exception as exc:
        raise EncryptionError(f"Encryption failed: {exc}") from exc


def decrypt_value(ciphertext: str, key: str | None = None) -> str:
    """Decrypt *ciphertext* and return the original plaintext string."""
    f = _get_fernet(key)
    try:
        plaintext = f.decrypt(ciphertext.encode())
        return plaintext.decode()
    except InvalidToken as exc:
        raise EncryptionError("Decryption failed: invalid token or wrong key.") from exc
    except Exception as exc:
        raise EncryptionError(f"Decryption failed: {exc}") from exc


def encrypt_dict(env: Dict[str, str], key: str | None = None) -> Dict[str, str]:
    """Return a new dict with every value encrypted."""
    return {k: encrypt_value(v, key) for k, v in env.items()}


def decrypt_dict(env: Dict[str, str], key: str | None = None) -> Dict[str, str]:
    """Return a new dict with every value decrypted."""
    return {k: decrypt_value(v, key) for k, v in env.items()}
