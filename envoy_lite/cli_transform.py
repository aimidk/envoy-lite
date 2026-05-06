"""CLI sub-command: envoy-transform — apply value transformers to an env file."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envoy_lite.loader import load_env_file
from envoy_lite.transformer import TransformError, transform_dict


def build_transform_parser(
    parent: "argparse._SubParsersAction | None" = None,
) -> argparse.ArgumentParser:
    kwargs = dict(
        prog="envoy-transform",
        description="Apply named transformers to env-file values.",
    )
    if parent is not None:
        parser = parent.add_parser("transform", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument(
        "-f", "--file", default=".env", help="Path to .env file (default: .env)"
    )
    parser.add_argument(
        "-t",
        "--transformer",
        dest="transformers",
        action="append",
        default=[],
        metavar="NAME",
        help="Transformer to apply (repeatable, applied in order)",
    )
    parser.add_argument(
        "-k",
        "--key",
        dest="keys",
        action="append",
        default=None,
        metavar="KEY",
        help="Restrict transformation to these keys (repeatable)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print transformed vars without modifying anything",
    )
    return parser


def cmd_transform(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        env = load_env_file(args.file)
    except FileNotFoundError:
        err.write(f"error: file not found: {args.file}\n")
        return 1

    if not args.transformers:
        err.write("error: at least one --transformer is required\n")
        return 1

    try:
        result = transform_dict(env, args.transformers, keys=args.keys)
    except TransformError as exc:
        err.write(f"error: {exc}\n")
        return 1

    for key in sorted(result):
        out.write(f"{key}={result[key]}\n")
    return 0


def main(argv: List[str] | None = None) -> None:
    parser = build_transform_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_transform(args))


if __name__ == "__main__":
    main()
