"""CLI sub-command: group / filter env vars by prefix, suffix, or pattern."""

from __future__ import annotations

import argparse
import json
import sys

from envoy_lite.loader import load_env_file
from envoy_lite.grouper import (
    GroupError,
    filter_by_prefix,
    filter_by_suffix,
    filter_by_pattern,
)


def build_group_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envoy-group",
        description="Filter environment variables by prefix, suffix, or pattern.",
    )
    parser = parent.add_parser("group", **kwargs) if parent else argparse.ArgumentParser(**kwargs)

    parser.add_argument("env_file", help="Path to .env file")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prefix", metavar="PREFIX", help="Keep keys starting with PREFIX")
    mode.add_argument("--suffix", metavar="SUFFIX", help="Keep keys ending with SUFFIX")
    mode.add_argument("--pattern", metavar="REGEX", help="Keep keys matching REGEX (full match)")

    parser.add_argument(
        "--strip",
        action="store_true",
        default=False,
        help="Strip the matched prefix/suffix from output key names",
    )
    parser.add_argument(
        "--format",
        choices=["dotenv", "json"],
        default="dotenv",
        help="Output format (default: dotenv)",
    )
    return parser


def cmd_group(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.env_file)
    except FileNotFoundError:
        print(f"error: file not found: {args.env_file}", file=sys.stderr)
        return 1

    try:
        if args.prefix:
            result = filter_by_prefix(env, args.prefix, strip=args.strip)
        elif args.suffix:
            result = filter_by_suffix(env, args.suffix, strip=args.strip)
        else:
            result = filter_by_pattern(env, args.pattern)
    except GroupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        for key in sorted(result):
            print(f"{key}={result[key]}")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_group_parser()
    args = parser.parse_args()
    sys.exit(cmd_group(args))


if __name__ == "__main__":  # pragma: no cover
    main()
