"""CLI entry-point for the masker module."""

from __future__ import annotations

import argparse
import sys

from envoy_lite.loader import load_env_file
from envoy_lite.masker import MaskError, mask_dict


def build_mask_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    kwargs = dict(
        prog="envoy-mask",
        description="Print env vars with sensitive values partially masked.",
    )
    parser = parent.add_parser("mask", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", help="Path to the .env file")
    parser.add_argument(
        "--keys", nargs="+", metavar="KEY",
        help="Keys to mask (default: all keys)",
    )
    parser.add_argument(
        "--strategy", choices=["suffix", "middle"], default="suffix",
        help="Masking strategy (default: suffix)",
    )
    parser.add_argument(
        "--visible", type=int, default=4,
        help="Number of characters to leave visible (default: 4)",
    )
    parser.add_argument(
        "--char", default="*",
        help="Mask character (default: *)",
    )
    return parser


def cmd_mask(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    try:
        masked = mask_dict(
            env,
            keys=args.keys,
            strategy=args.strategy,
            visible=args.visible,
            char=args.char,
        )
    except MaskError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for key in sorted(masked):
        print(f"{key}={masked[key]}")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_mask_parser()
    args = parser.parse_args()
    sys.exit(cmd_mask(args))


if __name__ == "__main__":  # pragma: no cover
    main()
