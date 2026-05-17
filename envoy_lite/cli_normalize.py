"""CLI entry-point for the normalize sub-command."""

from __future__ import annotations

import argparse
import sys

from envoy_lite.loader import load_env_file
from envoy_lite.normalizer import NormalizeError, normalize_dict


def build_normalize_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: E501
    kwargs = dict(
        prog="envoy-lite normalize",
        description="Normalize keys and values in an env file.",
    )
    parser = (
        parent.add_parser("normalize", **kwargs)
        if parent is not None
        else argparse.ArgumentParser(**kwargs)
    )
    parser.add_argument("file", help="Path to the .env file.")
    parser.add_argument(
        "--no-uppercase",
        dest="uppercase",
        action="store_false",
        default=True,
        help="Do not convert keys to uppercase (default: convert).",
    )
    parser.add_argument(
        "--collapse-whitespace",
        action="store_true",
        default=False,
        help="Collapse internal whitespace in values to a single space.",
    )
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        default=False,
        help="Silently drop keys that cannot be normalized.",
    )
    return parser


def cmd_normalize(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    try:
        normalized = normalize_dict(
            env,
            uppercase=args.uppercase,
            collapse_whitespace=args.collapse_whitespace,
            skip_errors=args.skip_errors,
        )
    except NormalizeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for key, value in sorted(normalized.items()):
        print(f"{key}={value}")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = build_normalize_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_normalize(args))


if __name__ == "__main__":  # pragma: no cover
    main()
