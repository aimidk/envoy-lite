"""Tests for envoy_lite.cli."""

import os
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envoy_lite.cli import build_parser, main


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        textwrap.dedent(
            """\
            APP_ENV=development
            DEBUG=true
            PORT=8080
            """
        )
    )
    return p


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.env_file == ".env"
    assert args.override is False
    assert args.dry_run is False
    assert args.command == []


def test_build_parser_custom_file():
    parser = build_parser()
    args = parser.parse_args(["-f", "prod.env", "echo", "hi"])
    assert args.env_file == "prod.env"
    assert args.command == ["echo", "hi"]


def test_dry_run_prints_vars(env_file: Path, capsys):
    ret = main(["-f", str(env_file), "--dry-run"])
    assert ret == 0
    out = capsys.readouterr().out
    assert "APP_ENV=development" in out
    assert "DEBUG=true" in out
    assert "PORT=8080" in out


def test_dry_run_sorted_output(env_file: Path, capsys):
    main(["-f", str(env_file), "--dry-run"])
    lines = capsys.readouterr().out.strip().splitlines()
    keys = [line.split("=")[0] for line in lines]
    assert keys == sorted(keys)


def test_missing_env_file_returns_1(tmp_path: Path, capsys):
    ret = main(["-f", str(tmp_path / "nonexistent.env"), "--dry-run"])
    assert ret == 1
    assert "not found" in capsys.readouterr().err


def test_no_command_returns_1(env_file: Path):
    ret = main(["-f", str(env_file)])
    assert ret == 1


def test_command_receives_env_vars(env_file: Path):
    mock_result = MagicMock(returncode=0)
    with patch("envoy_lite.cli.subprocess.run", return_value=mock_result) as mock_run:
        ret = main(["-f", str(env_file), "printenv", "APP_ENV"])
    assert ret == 0
    call_env = mock_run.call_args.kwargs["env"]
    assert call_env["APP_ENV"] == "development"


def test_command_not_found_returns_127(env_file: Path, capsys):
    with patch("envoy_lite.cli.subprocess.run", side_effect=FileNotFoundError):
        ret = main(["-f", str(env_file), "no-such-binary"])
    assert ret == 127
    assert "command not found" in capsys.readouterr().err


def test_override_flag_merges_env(env_file: Path):
    os.environ["PORT"] = "9999"
    try:
        mock_result = MagicMock(returncode=0)
        with patch("envoy_lite.cli.subprocess.run", return_value=mock_result) as mock_run:
            main(["-f", str(env_file), "--override", "printenv", "PORT"])
        call_env = mock_run.call_args.kwargs["env"]
        assert call_env["PORT"] == "8080"
    finally:
        os.environ.pop("PORT", None)
