"""Simple file templating: render a template file using env vars."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

_TMPL_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\|\s*([^}]*))?\}\}")


class TemplateRenderError(Exception):
    """Raised when a required placeholder has no value."""


def render_string(template: str, env: Mapping[str, str]) -> str:
    """Render *template* by substituting ``{{ VAR }}`` placeholders.

    Supports an optional default via ``{{ VAR | default }}``.
    Raises :class:`TemplateRenderError` for missing variables with no default.
    """

    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        name = m.group(1)
        default = m.group(2)
        if name in env:
            return env[name]
        if default is not None:
            return default.strip()
        raise TemplateRenderError(
            f"Template variable '{name}' is not defined and has no default."
        )

    return _TMPL_RE.sub(_replace, template)


def render_file(src: str | Path, env: Mapping[str, str]) -> str:
    """Read *src* from disk and render it with *env*."""
    content = Path(src).read_text(encoding="utf-8")
    return render_string(content, env)


def render_to_file(
    src: str | Path, dest: str | Path, env: Mapping[str, str]
) -> None:
    """Render *src* and write the result to *dest*."""
    rendered = render_file(src, env)
    Path(dest).write_text(rendered, encoding="utf-8")
