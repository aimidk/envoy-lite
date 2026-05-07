"""Tests for envoy_lite.pinner and envoy_lite.cli_pin."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy_lite.pinner import PinError, diff_pin, load_pin, pin_env
from envoy_lite.cli_pin import build_pin_parser, cmd_pin


# ---------------------------------------------------------------------------
# pin_env / load_pin
# ---------------------------------------------------------------------------

def test_pin_env_creates_file(tmp_path: Path) -> None:
    lock = tmp_path / ".env.lock"
    pin_env({"FOO": "bar", "BAZ": "1"}, lock)
    assert lock.exists()


def test_pin_env_content_is_sorted_json(tmp_path: Path) -> None:
    lock = tmp_path / ".env.lock"
    pin_env({"Z": "last", "A": "first"}, lock)
    data = json.loads(lock.read_text())
    assert list(data.keys()) == ["A", "Z"]


def test_load_pin_roundtrip(tmp_path: Path) -> None:
    lock = tmp_path / ".env.lock"
    original = {"KEY": "value", "NUM": "42"}
    pin_env(original, lock)
    assert load_pin(lock) == original


def test_load_pin_missing_file(tmp_path: Path) -> None:
    with pytest.raises(PinError, match="not found"):
        load_pin(tmp_path / "ghost.lock")


def test_load_pin_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.lock"
    bad.write_text("not json")
    with pytest.raises(PinError, match="not valid JSON"):
        load_pin(bad)


def test_load_pin_non_string_values(tmp_path: Path) -> None:
    bad = tmp_path / "bad.lock"
    bad.write_text(json.dumps({"KEY": 123}))
    with pytest.raises(PinError, match="flat JSON object"):
        load_pin(bad)


# ---------------------------------------------------------------------------
# diff_pin
# ---------------------------------------------------------------------------

def test_diff_pin_no_changes() -> None:
    assert diff_pin({"A": "1"}, {"A": "1"}) == {}


def test_diff_pin_added_key() -> None:
    result = diff_pin({"A": "1", "B": "2"}, {"A": "1"})
    assert result == {"B": {"current": "2", "pinned": None}}


def test_diff_pin_removed_key() -> None:
    result = diff_pin({"A": "1"}, {"A": "1", "B": "old"})
    assert result == {"B": {"current": None, "pinned": "old"}}


def test_diff_pin_changed_value() -> None:
    result = diff_pin({"A": "new"}, {"A": "old"})
    assert result == {"A": {"current": "new", "pinned": "old"}}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("HELLO=world\nNUM=99\n")
    return f


def _args(parser, *argv):
    return parser.parse_args(list(argv))


def test_cmd_pin_save(env_file: Path, tmp_path: Path) -> None:
    lock = tmp_path / ".env.lock"
    parser = build_pin_parser()
    args = _args(parser, "save", "--env-file", str(env_file), "--pin-file", str(lock))
    rc = cmd_pin(args)
    assert rc == 0
    assert lock.exists()


def test_cmd_pin_show(env_file: Path, tmp_path: Path, capsys) -> None:
    lock = tmp_path / ".env.lock"
    pin_env({"X": "1"}, lock)
    parser = build_pin_parser()
    args = _args(parser, "show", "--pin-file", str(lock))
    rc = cmd_pin(args)
    assert rc == 0
    assert "X=1" in capsys.readouterr().out


def test_cmd_pin_diff_no_changes(env_file: Path, tmp_path: Path, capsys) -> None:
    lock = tmp_path / ".env.lock"
    pin_env({"HELLO": "world", "NUM": "99"}, lock)
    parser = build_pin_parser()
    args = _args(parser, "diff", "--env-file", str(env_file), "--pin-file", str(lock))
    rc = cmd_pin(args)
    assert rc == 0
    assert "No differences" in capsys.readouterr().out


def test_cmd_pin_diff_with_changes(env_file: Path, tmp_path: Path, capsys) -> None:
    lock = tmp_path / ".env.lock"
    pin_env({"HELLO": "old", "NUM": "99"}, lock)
    parser = build_pin_parser()
    args = _args(parser, "diff", "--env-file", str(env_file), "--pin-file", str(lock))
    rc = cmd_pin(args)
    assert rc == 1
    out = capsys.readouterr().out
    assert "HELLO" in out


def test_cmd_pin_save_bad_path(tmp_path: Path, capsys) -> None:
    env = tmp_path / ".env"
    env.write_text("A=1\n")
    parser = build_pin_parser()
    args = _args(parser, "save", "--env-file", str(env), "--pin-file", "/no/such/dir/x.lock")
    rc = cmd_pin(args)
    assert rc == 2
    assert "error" in capsys.readouterr().err
