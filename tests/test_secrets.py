"""Tests for envoy_lite.secrets module."""

import os
from pathlib import Path

import pytest

from envoy_lite.secrets import (
    inject_secrets,
    register_backend,
    resolve_secret,
)


# ---------------------------------------------------------------------------
# resolve_secret
# ---------------------------------------------------------------------------


def test_resolve_non_secret_passthrough():
    assert resolve_secret("plain_value") == "plain_value"
    assert resolve_secret("https://example.com") == "https://example.com"


def test_resolve_file_backend(tmp_path: Path):
    secret_file = tmp_path / "my_token"
    secret_file.write_text("super-secret-token\n")
    uri = f"secret://file/{secret_file}"
    assert resolve_secret(uri) == "super-secret-token"


def test_resolve_file_backend_missing(tmp_path: Path):
    uri = f"secret://file/{tmp_path}/nonexistent"
    with pytest.raises(FileNotFoundError):
        resolve_secret(uri)


def test_resolve_unknown_provider():
    with pytest.raises(ValueError, match="Unknown secret provider"):
        resolve_secret("secret://vault/my-key")


# ---------------------------------------------------------------------------
# register_backend + custom provider
# ---------------------------------------------------------------------------


def test_register_custom_backend():
    store = {"api-key": "my-api-key-value"}
    register_backend("mock", lambda key: store[key])
    assert resolve_secret("secret://mock/api-key") == "my-api-key-value"


def test_register_custom_backend_key_error():
    register_backend("mock2", lambda key: (_ for _ in ()).throw(KeyError(key)))
    with pytest.raises(KeyError):
        resolve_secret("secret://mock2/missing")


# ---------------------------------------------------------------------------
# inject_secrets
# ---------------------------------------------------------------------------


def test_inject_secrets_resolves_values(tmp_path: Path, monkeypatch):
    secret_file = tmp_path / "db_pass"
    secret_file.write_text("s3cr3t")

    env = {
        "DB_HOST": "localhost",
        "DB_PASS": f"secret://file/{secret_file}",
    }
    result = inject_secrets(env)
    assert result["DB_HOST"] == "localhost"
    assert result["DB_PASS"] == "s3cr3t"


def test_inject_secrets_updates_os_environ(tmp_path: Path, monkeypatch):
    secret_file = tmp_path / "token"
    secret_file.write_text("tok123")
    monkeypatch.delenv("INJECTED_TOKEN", raising=False)

    inject_secrets({"INJECTED_TOKEN": f"secret://file/{secret_file}"})
    assert os.environ["INJECTED_TOKEN"] == "tok123"
