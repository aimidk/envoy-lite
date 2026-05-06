"""Tests for envoy_lite.encryptor."""

from __future__ import annotations

import os
import pytest

pytest.importorskip("cryptography", reason="cryptography package not installed")

from envoy_lite.encryptor import (
    EncryptionError,
    MissingKeyError,
    decrypt_dict,
    decrypt_value,
    encrypt_dict,
    encrypt_value,
    generate_key,
    ENV_KEY_VAR,
)


@pytest.fixture()
def key() -> str:
    return generate_key()


# ---------------------------------------------------------------------------
# generate_key
# ---------------------------------------------------------------------------

def test_generate_key_returns_string(key):
    assert isinstance(key, str)
    assert len(key) > 0


def test_generate_key_unique():
    assert generate_key() != generate_key()


# ---------------------------------------------------------------------------
# encrypt_value / decrypt_value round-trip
# ---------------------------------------------------------------------------

def test_encrypt_returns_string(key):
    ct = encrypt_value("hello", key=key)
    assert isinstance(ct, str)
    assert ct != "hello"


def test_roundtrip(key):
    plaintext = "super-secret-value"
    assert decrypt_value(encrypt_value(plaintext, key=key), key=key) == plaintext


def test_roundtrip_empty_string(key):
    assert decrypt_value(encrypt_value("", key=key), key=key) == ""


def test_roundtrip_unicode(key):
    plaintext = "caf\u00e9 \U0001f511"
    assert decrypt_value(encrypt_value(plaintext, key=key), key=key) == plaintext


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv(ENV_KEY_VAR, raising=False)
    with pytest.raises(MissingKeyError):
        encrypt_value("x")


def test_key_from_env_var(monkeypatch):
    k = generate_key()
    monkeypatch.setenv(ENV_KEY_VAR, k)
    ct = encrypt_value("from-env")
    assert decrypt_value(ct) == "from-env"


def test_invalid_key_raises():
    with pytest.raises(EncryptionError):
        encrypt_value("x", key="not-a-valid-fernet-key")


def test_decrypt_wrong_key_raises(key):
    ct = encrypt_value("secret", key=key)
    other_key = generate_key()
    with pytest.raises(EncryptionError, match="invalid token or wrong key"):
        decrypt_value(ct, key=other_key)


def test_decrypt_garbage_raises(key):
    with pytest.raises(EncryptionError):
        decrypt_value("not-valid-ciphertext", key=key)


# ---------------------------------------------------------------------------
# encrypt_dict / decrypt_dict
# ---------------------------------------------------------------------------

def test_encrypt_dict_roundtrip(key):
    env = {"DB_PASS": "s3cr3t", "API_KEY": "abc123", "PORT": "5432"}
    encrypted = encrypt_dict(env, key=key)
    assert set(encrypted.keys()) == set(env.keys())
    assert all(encrypted[k] != v for k, v in env.items())
    assert decrypt_dict(encrypted, key=key) == env


def test_encrypt_dict_empty(key):
    assert encrypt_dict({}, key=key) == {}
    assert decrypt_dict({}, key=key) == {}
