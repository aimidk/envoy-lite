"""Tests for envoy_lite.exporter."""

import json
import pytest

from envoy_lite.exporter import (
    UnsupportedFormatError,
    export_env,
    to_csv,
    to_dotenv,
    to_export_shell,
    to_json,
)

SAMPLE = {"DB_HOST": "localhost", "API_KEY": "abc123", "PORT": "5432"}


# ---------------------------------------------------------------------------
# to_export_shell
# ---------------------------------------------------------------------------

class TestToExportShell:
    def test_lines_start_with_export(self):
        result = to_export_shell({"FOO": "bar"})
        assert result.startswith("export FOO=")

    def test_value_is_double_quoted(self):
        result = to_export_shell({"X": "hello world"})
        assert 'X="hello world"' in result

    def test_inner_double_quote_escaped(self):
        result = to_export_shell({"MSG": 'say "hi"'})
        assert '\\"hi\\"' in result

    def test_multiple_keys_sorted(self):
        lines = to_export_shell(SAMPLE).splitlines()
        keys = [ln.split("=")[0].replace("export ", "") for ln in lines]
        assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# to_dotenv
# ---------------------------------------------------------------------------

class TestToDotenv:
    def test_no_export_prefix(self):
        result = to_dotenv({"FOO": "bar"})
        assert not result.startswith("export")

    def test_key_value_format(self):
        result = to_dotenv({"FOO": "bar"})
        assert result == 'FOO="bar"'

    def test_sorted_output(self):
        lines = to_dotenv(SAMPLE).splitlines()
        keys = [ln.split("=")[0] for ln in lines]
        assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# to_json
# ---------------------------------------------------------------------------

class TestToJson:
    def test_valid_json(self):
        result = to_json(SAMPLE)
        parsed = json.loads(result)
        assert parsed == SAMPLE

    def test_sorted_keys(self):
        result = to_json(SAMPLE)
        parsed = json.loads(result)
        assert list(parsed.keys()) == sorted(parsed.keys())


# ---------------------------------------------------------------------------
# to_csv
# ---------------------------------------------------------------------------

class TestToCsv:
    def test_header_row(self):
        result = to_csv({"A": "1"})
        assert result.splitlines()[0] == "key,value"

    def test_data_row(self):
        result = to_csv({"A": "1"})
        assert "A,1" in result

    def test_sorted_rows(self):
        rows = to_csv(SAMPLE).splitlines()[1:]  # skip header
        keys = [r.split(",")[0] for r in rows]
        assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# export_env (dispatcher)
# ---------------------------------------------------------------------------

class TestExportEnv:
    def test_default_format_is_dotenv(self):
        result = export_env({"K": "v"})
        assert result == 'K="v"'

    def test_unknown_format_raises(self):
        with pytest.raises(UnsupportedFormatError):
            export_env({"K": "v"}, fmt="xml")

    def test_keys_allowlist_filters(self):
        result = export_env(SAMPLE, fmt="dotenv", keys=["PORT"])
        assert "PORT" in result
        assert "DB_HOST" not in result
        assert "API_KEY" not in result

    def test_keys_missing_from_env_silently_ignored(self):
        result = export_env({"A": "1"}, fmt="dotenv", keys=["A", "MISSING"])
        assert "MISSING" not in result

    def test_json_format_dispatched(self):
        result = export_env({"Z": "9"}, fmt="json")
        assert json.loads(result) == {"Z": "9"}
