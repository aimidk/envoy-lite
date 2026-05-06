"""CLI sub-command: render a template file with loaded env vars."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy_lite.loader import load_env_file
from envoy_lite.templater import TemplateRenderError, render_string


def build_template_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envoy-template",
        description="Render a template file using variables from an env file.",
    )
    if parent is not None:
        parser = parent.add_parser("template", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument(
        "template",
        metavar="TEMPLATE",
        help="Path to the template file (uses {{ VAR }} syntax).",
    )
    parser.add_argument(
        "-e",
        "--env-file",
        default=".env",
        metavar="FILE",
        help="Env file to load (default: .env).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        metavar="FILE",
        help="Write rendered output to FILE instead of stdout.",
    )
    return parser


def cmd_template(args: argparse.Namespace) -> int:
    env = load_env_file(args.env_file)
    template_text = Path(args.template).read_text(encoding="utf-8")
    try:
        rendered = render_string(template_text, env)
    except TemplateRenderError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_template_parser()
    args = parser.parse_args()
    sys.exit(cmd_template(args))
