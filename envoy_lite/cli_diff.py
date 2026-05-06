"""CLI entry point for diffing two env files."""

from __future__ import annotations

import argparse
import sys

from envoy_lite.differ import diff_files


def build_diff_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    kwargs = dict(
        prog="envoy-diff",
        description="Show differences between two .env files.",
    )
    if parent is not None:
        parser = parent.add_parser("diff", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("base", help="Base .env file")
    parser.add_argument("other", help="Other .env file to compare against base")
    parser.add_argument(
        "--no-override",
        dest="override",
        action="store_false",
        default=True,
        help="Do not allow later keys to override earlier ones within a file",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if there are any differences",
    )
    return parser


def cmd_diff(args: argparse.Namespace) -> int:
    try:
        result = diff_files(args.base, args.other, override=args.override)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(result.summary())
    if args.exit_code and result.has_changes:
        return 1
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = build_diff_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_diff(args))


if __name__ == "__main__":
    main()
