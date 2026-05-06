"""CLI sub-command: envoy-lite redact — print env vars with secrets masked."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envoy_lite.loader import load_env_file
from envoy_lite.redactor import Redactor


def build_redact_parser(subparsers=None) -> argparse.ArgumentParser:
    kwargs = dict(
        description="Print env file variables with sensitive values masked."
    )
    if subparsers is not None:
        parser = subparsers.add_parser("redact", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envoy-lite-redact", **kwargs)

    parser.add_argument(
        "--file", "-f",
        default=".env",
        metavar="FILE",
        help="Path to the .env file (default: .env)",
    )
    parser.add_argument(
        "--mask",
        default="***",
        help="Replacement string for sensitive values (default: ***)",
    )
    parser.add_argument(
        "--extra-pattern",
        dest="extra_patterns",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Additional regex pattern to treat as sensitive (repeatable)",
    )
    parser.add_argument(
        "--show-keys-only",
        action="store_true",
        help="Only print the names of sensitive keys, not all variables",
    )
    return parser


def cmd_redact(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    redactor = Redactor(extra_patterns=args.extra_patterns, mask=args.mask)

    if args.show_keys_only:
        sensitive = [k for k in sorted(env) if redactor.is_sensitive(k)]
        for key in sensitive:
            print(key)
        return 0

    redacted = redactor.redact_dict(env)
    for key in sorted(redacted):
        print(f"{key}={redacted[key]}")
    return 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_redact_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_redact(args))


if __name__ == "__main__":  # pragma: no cover
    main()
