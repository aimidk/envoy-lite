"""CLI entry point for comparing two .env files."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envoy_lite.comparator import compare_dicts
from envoy_lite.loader import load_env_file


def build_compare_parser(
    parser: Optional[argparse.ArgumentParser] = None,
) -> argparse.ArgumentParser:
    if parser is None:
        parser = argparse.ArgumentParser(
            prog="envoy-compare",
            description="Compare two .env files and report differences.",
        )
    parser.add_argument("left", help="Base .env file (left side)")
    parser.add_argument("right", help="New .env file (right side)")
    parser.add_argument(
        "--hide-unchanged",
        action="store_true",
        default=False,
        help="Suppress unchanged keys from output",
    )
    parser.add_argument(
        "--only",
        choices=["added", "removed", "changed"],
        default=None,
        help="Show only keys with this status",
    )
    return parser


def cmd_compare(args: argparse.Namespace) -> int:
    left_env = load_env_file(args.left)
    right_env = load_env_file(args.right)

    include_unchanged = not args.hide_unchanged
    report = compare_dicts(left_env, right_env, include_unchanged=include_unchanged)

    entries = report.entries
    if args.only:
        entries = [e for e in entries if e.status == args.only]

    symbols = {"added": "+", "removed": "-", "changed": "~", "unchanged": " "}

    for entry in entries:
        sym = symbols[entry.status]
        if entry.status == "changed":
            print(f"{sym} {entry.key}: {entry.left!r} -> {entry.right!r}")
        elif entry.status == "added":
            print(f"{sym} {entry.key}={entry.right!r}")
        elif entry.status == "removed":
            print(f"{sym} {entry.key}={entry.left!r}")
        else:
            print(f"{sym} {entry.key}={entry.left!r}")

    print()
    print(report.summary())
    return 0 if not report.has_differences() else 1


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_compare_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_compare(args))


if __name__ == "__main__":
    main()
