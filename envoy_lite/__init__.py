"""envoy-lite: Lightweight environment variable manager with secret injection."""

from envoy_lite.loader import load_env_file
from envoy_lite.secrets import inject_secrets, register_backend, resolve_secret

__version__ = "0.1.0"
__all__ = [
    "load_env_file",
    "inject_secrets",
    "register_backend",
    "resolve_secret",
    "load",
]


def load(
    path: str = ".env",
    override: bool = False,
    expand: bool = True,
    inject: bool = True,
) -> dict:
    """
    Convenience entry-point: load a .env file and optionally inject secrets.

    Args:
        path: Path to the .env file (default: ".env").
        override: Overwrite existing os.environ entries.
        expand: Expand $VAR references in values.
        inject: Resolve secret:// URIs after loading.

    Returns:
        Final dict of environment variables (secrets resolved if inject=True).
    """
    env = load_env_file(path=path, override=override, expand=expand)
    if inject:
        env = inject_secrets(env)
    return env
