"""Lint .env files for common issues and style violations."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LintIssue:
    line_no: int
    code: str
    message: str
    severity: str = "warning"  # "error" | "warning" | "info"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] line {self.line_no} ({self.code}): {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    def summary(self) -> str:
        errors = sum(1 for i in self.issues if i.severity == "error")
        warnings = sum(1 for i in self.issues if i.severity == "warning")
        return f"{errors} error(s), {warnings} warning(s)"


_VALID_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')
_LOWER_KEY_RE = re.compile(r'^[a-z]')


def lint_lines(lines: List[str]) -> LintResult:
    result = LintResult()
    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        # Skip blank lines and comments
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Remove optional export prefix
        working = stripped
        if working.startswith("export "):
            working = working[7:].lstrip()

        if "=" not in working:
            result.issues.append(LintIssue(lineno, "E001", f"No '=' found: {line!r}", "error"))
            continue

        key, _, value = working.partition("=")
        key = key.strip()

        if not key:
            result.issues.append(LintIssue(lineno, "E002", "Empty key name", "error"))
            continue

        if not _VALID_KEY_RE.match(key):
            if _LOWER_KEY_RE.match(key):
                result.issues.append(LintIssue(lineno, "W001", f"Key '{key}' uses lowercase; prefer UPPER_SNAKE_CASE", "warning"))
            else:
                result.issues.append(LintIssue(lineno, "W002", f"Key '{key}' contains unusual characters", "warning"))

        if key in seen_keys:
            result.issues.append(LintIssue(lineno, "W003", f"Duplicate key '{key}' (first seen on line {seen_keys[key]})", "warning"))
        else:
            seen_keys[key] = lineno

        if value != value.strip() and not (value.startswith('"') or value.startswith("'")):
            result.issues.append(LintIssue(lineno, "W004", f"Value for '{key}' has leading/trailing whitespace", "warning"))

    return result


def lint_file(path: str) -> LintResult:
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    return lint_lines(lines)
