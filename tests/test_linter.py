"""Tests for envoy_lite.linter."""
from __future__ import annotations

import pytest

from envoy_lite.linter import lint_lines, lint_file, LintIssue, LintResult


def _codes(result: LintResult) -> list[str]:
    return [i.code for i in result.issues]


def test_empty_file_no_issues():
    assert not lint_lines([]).has_issues


def test_comment_lines_ignored():
    result = lint_lines(["# just a comment\n", "\n"])
    assert not result.has_issues


def test_simple_valid_pair():
    result = lint_lines(["FOO=bar\n"])
    assert not result.has_issues


def test_export_prefix_accepted():
    result = lint_lines(["export BAR=baz\n"])
    assert not result.has_issues


def test_no_equals_is_error():
    result = lint_lines(["BADLINE\n"])
    assert "E001" in _codes(result)
    assert result.has_errors


def test_empty_key_is_error():
    result = lint_lines(["=value\n"])
    assert "E002" in _codes(result)


def test_lowercase_key_warns():
    result = lint_lines(["my_var=hello\n"])
    assert "W001" in _codes(result)
    assert not result.has_errors


def test_duplicate_key_warns():
    result = lint_lines(["FOO=1\n", "FOO=2\n"])
    assert "W003" in _codes(result)


def test_duplicate_key_references_first_line():
    result = lint_lines(["FOO=1\n", "FOO=2\n"])
    issue = next(i for i in result.issues if i.code == "W003")
    assert "line 1" in issue.message


def test_trailing_whitespace_in_value_warns():
    result = lint_lines(["FOO=hello   \n"])
    assert "W004" in _codes(result)


def test_quoted_value_whitespace_not_warned():
    result = lint_lines(['FOO="hello world"\n'])
    assert "W004" not in _codes(result)


def test_summary_counts():
    result = lint_lines(["BADLINE\n", "foo=1\n", "FOO=1\n", "FOO=2\n"])
    summary = result.summary()
    assert "1 error" in summary


def test_has_errors_false_for_warnings_only():
    result = lint_lines(["foo=bar\n"])
    assert not result.has_errors
    assert result.has_issues


def test_lint_issue_str():
    issue = LintIssue(3, "W001", "some message", "warning")
    s = str(issue)
    assert "WARNING" in s
    assert "line 3" in s
    assert "W001" in s


def test_lint_file_reads_from_disk(tmp_path):
    env = tmp_path / ".env"
    env.write_text("GOOD=1\nBAD_lower=2\n")
    result = lint_file(str(env))
    assert "W001" in _codes(result)


def test_lint_file_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        lint_file(str(tmp_path / "nonexistent.env"))
