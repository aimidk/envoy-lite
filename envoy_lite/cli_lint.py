"""CLI entry-point for the env-file linter."""
from __future__ import annotations

import argparse
import sys

from .linter import lint_file, LintResult


def build_lint_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    kwargs = dict(
        prog="envoy-lint",
        description="Lint a .env file for common issues.",
    )
    if parent is not None:
        parser = parent.add_parser("lint", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument(
        "file",
        metavar="FILE",
        help="Path to the .env file to lint.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with code 1 if any warnings are present (not just errors).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress per-issue output; only print the summary.",
    )
    return parser


def cmd_lint(args: argparse.Namespace) -> int:
    try:
        result: LintResult = lint_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2

    if not args.quiet:
        for issue in result.issues:
            print(issue)

    print(result.summary())

    if args.strict and result.has_issues:
        return 1
    if result.has_errors:
        return 1
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = build_lint_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_lint(args))


if __name__ == "__main__":  # pragma: no cover
    main()
