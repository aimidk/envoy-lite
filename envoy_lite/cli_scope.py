"""CLI entry-point for scope filtering commands."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from envoy_lite.loader import load_env_file
from envoy_lite.scoper import ScopeError, list_scopes, merge_scopes, scope_filter


def build_scope_parser(subparsers=None):
    """Build (or register) the argument parser for the *scope* sub-command."""
    kwargs = dict(
        description="Filter environment variables by scope prefix.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    if subparsers is not None:
        parser = subparsers.add_parser("scope", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("file", help="Path to the .env file.")
    parser.add_argument(
        "--scope",
        metavar="SCOPE",
        help="Scope name to filter (e.g. APP, DB). Omit to list available scopes.",
    )
    parser.add_argument(
        "--separator",
        default="__",
        metavar="SEP",
        help="Separator between scope and key name.",
    )
    parser.add_argument(
        "--no-strip",
        action="store_true",
        default=False,
        help="Keep the scope prefix in output keys.",
    )
    parser.add_argument(
        "--merge",
        nargs="+",
        metavar="SCOPE",
        help="Merge multiple scopes (later scopes win).",
    )
    parser.add_argument(
        "--format",
        choices=["dotenv", "json"],
        default="dotenv",
        help="Output format.",
    )
    return parser


def cmd_scope(args) -> int:
    """Execute the scope command; returns exit code."""
    try:
        env = load_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    sep = args.separator
    strip = not args.no_strip

    try:
        if args.merge:
            result = merge_scopes(env, args.merge, separator=sep, strip_prefix=strip)
        elif args.scope:
            result = scope_filter(env, args.scope, strip_prefix=strip, separator=sep)
        else:
            scopes = list_scopes(env, separator=sep)
            for s in scopes:
                print(s)
            return 0
    except ScopeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        for k, v in sorted(result.items()):
            print(f"{k}={v}")
    return 0


def main(argv=None):
    parser = build_scope_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_scope(args))


if __name__ == "__main__":
    main()
