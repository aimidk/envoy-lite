"""File watcher for hot-reloading .env files during local dev."""

import os
import time
import threading
from typing import Callable, Optional

from envoy_lite.loader import load_env_file


class EnvFileWatcher:
    """Watches a .env file for changes and triggers a reload callback."""

    def __init__(
        self,
        filepath: str,
        callback: Callable[[dict], None],
        poll_interval: float = 1.0,
        override: bool = True,
    ):
        self.filepath = filepath
        self.callback = callback
        self.poll_interval = poll_interval
        self.override = override
        self._last_mtime: Optional[float] = None
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _get_mtime(self) -> Optional[float]:
        try:
            return os.path.getmtime(self.filepath)
        except FileNotFoundError:
            return None

    def _check_and_reload(self) -> None:
        mtime = self._get_mtime()
        if mtime is None:
            return
        if self._last_mtime is None or mtime != self._last_mtime:
            self._last_mtime = mtime
            try:
                env_vars = load_env_file(self.filepath, override=self.override)
                self.callback(env_vars)
            except Exception as exc:  # noqa: BLE001
                print(f"[envoy-lite] watcher reload error: {exc}")

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._check_and_reload()
            self._stop_event.wait(self.poll_interval)

    def start(self) -> None:
        """Start watching in a background daemon thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="envoy-lite-watcher")
        self._thread.start()

    def stop(self) -> None:
        """Stop the watcher thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self.poll_interval * 2)
            self._thread = None

    def __enter__(self) -> "EnvFileWatcher":
        self.start()
        return self

    def __exit__(self, *_) -> None:
        self.stop()


def watch_env_file(
    filepath: str,
    callback: Callable[[dict], None],
    poll_interval: float = 1.0,
    override: bool = True,
) -> EnvFileWatcher:
    """Convenience factory: create and start an EnvFileWatcher."""
    watcher = EnvFileWatcher(filepath, callback, poll_interval=poll_interval, override=override)
    watcher.start()
    return watcher
