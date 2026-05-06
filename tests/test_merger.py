"""Tests for envoy_lite.merger."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from envoy_lite.merger import MergeConflict, merge_env_files, merge_with_os_environ


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> str:
    path = directory / name
    path.write_text(textwrap.dedent(content))
    return str(path)


# ---------------------------------------------------------------------------
# merge_env_files
# ---------------------------------------------------------------------------


def test_merge_empty_list():
    assert merge_env_files([]) == {}


def test_merge_single_file(env_dir):
    p = _write(env_dir, ".env", "FOO=bar\nBAZ=qux\n")
    assert merge_env_files([p]) == {"FOO": "bar", "BAZ": "qux"}


def test_merge_override_true_later_wins(env_dir):
    p1 = _write(env_dir, ".env.base", "FOO=base\nSHARED=first\n")
    p2 = _write(env_dir, ".env.local", "SHARED=second\nBAR=local\n")
    result = merge_env_files([p1, p2], override=True)
    assert result["SHARED"] == "second"
    assert result["FOO"] == "base"
    assert result["BAR"] == "local"


def test_merge_override_false_earlier_wins(env_dir):
    p1 = _write(env_dir, ".env.base", "SHARED=first\n")
    p2 = _write(env_dir, ".env.local", "SHARED=second\n")
    result = merge_env_files([p1, p2], override=False)
    assert result["SHARED"] == "first"


def test_merge_strict_raises_on_conflict(env_dir):
    p1 = _write(env_dir, ".env.a", "KEY=one\n")
    p2 = _write(env_dir, ".env.b", "KEY=two\n")
    with pytest.raises(MergeConflict) as exc_info:
        merge_env_files([p1, p2], strict=True)
    assert exc_info.value.key == "KEY"
    assert len(exc_info.value.sources) == 2


def test_merge_strict_no_conflict_passes(env_dir):
    p1 = _write(env_dir, ".env.a", "A=1\n")
    p2 = _write(env_dir, ".env.b", "B=2\n")
    result = merge_env_files([p1, p2], strict=True)
    assert result == {"A": "1", "B": "2"}


def test_merge_missing_file_raises_by_default(env_dir):
    with pytest.raises(FileNotFoundError):
        merge_env_files([str(env_dir / "nonexistent.env")])


def test_merge_missing_ok_skips_file(env_dir):
    p = _write(env_dir, ".env", "REAL=yes\n")
    result = merge_env_files(
        [str(env_dir / "ghost.env"), p], missing_ok=True
    )
    assert result == {"REAL": "yes"}


# ---------------------------------------------------------------------------
# merge_with_os_environ
# ---------------------------------------------------------------------------


def test_os_environ_wins_by_default(env_dir):
    p = _write(env_dir, ".env", "MYVAR=from_file\n")
    fake_os = {"MYVAR": "from_os", "OTHER": "x"}
    result = merge_with_os_environ([p], os_environ=fake_os)
    assert result["MYVAR"] == "from_os"


def test_env_wins_flag(env_dir):
    p = _write(env_dir, ".env", "MYVAR=from_file\n")
    fake_os = {"MYVAR": "from_os"}
    result = merge_with_os_environ([p], os_environ=fake_os, env_wins=True)
    assert result["MYVAR"] == "from_file"


def test_merge_with_os_environ_uses_real_os_environ(env_dir, monkeypatch):
    monkeypatch.setenv("_ENVOY_TEST_KEY", "sentinel")
    p = _write(env_dir, ".env", "EXTRA=yes\n")
    result = merge_with_os_environ([p])
    assert result["_ENVOY_TEST_KEY"] == "sentinel"
    assert result["EXTRA"] == "yes"
