"""CLI sub-command: envoy-lite interpolate

Interpolates ${...} tokens in a .env file against the current OS environment
(plus any variables defined earlier in the file itself) and prints the result.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from envoy_lite.loader import load_env_file
from envoy_lite.interpolator import interpolate_dict, InterpolationError


def build_interpolate_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "interpolate",
        help="Expand ${VAR} tokens in a .env file and print the result.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=".env",
        help="Path to the .env file (default: .env).",
    )
    parser.add_argument(
        "--no-os-env",
        action="store_true",
        default=False,
        help="Do not seed resolution from the OS environment.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with code 1 on any unresolvable variable (default: warn).",
    )
    parser.set_defaults(func=cmd_interpolate)
    return parser


def cmd_interpolate(args: argparse.Namespace) -> int:
    """Execute the interpolate sub-command."""
    try:
        raw: dict = load_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    base_env = dict(os.environ) if not args.no_os_env else {}

    try:
        resolved = interpolate_dict(raw, base_env=base_env)
    except InterpolationError as exc:
        msg = f"interpolation error: {exc}"
        if args.strict:
            print(msg, file=sys.stderr)
            return 1
        print(f"warning: {msg}", file=sys.stderr)
        resolved = raw  # fall back to raw values

    for key in sorted(resolved):
        print(f"{key}={resolved[key]}")

    return 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(prog="envoy-lite-interpolate")
    subparsers = parser.add_subparsers(dest="command")
    build_interpolate_parser(subparsers)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    main()
