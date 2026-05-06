"""Tests for envoy_lite.watcher hot-reload functionality."""

import os
import time
import threading
import pytest

from envoy_lite.watcher import EnvFileWatcher, watch_env_file


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("FOO=bar\nBAZ=qux\n")
    return str(f)


def test_watcher_initial_load(env_file):
    received = []
    watcher = EnvFileWatcher(env_file, callback=received.append, poll_interval=0.05)
    watcher.start()
    time.sleep(0.2)
    watcher.stop()
    assert len(received) >= 1
    assert received[0].get("FOO") == "bar"


def test_watcher_detects_change(env_file):
    received = []
    watcher = EnvFileWatcher(env_file, callback=received.append, poll_interval=0.05)
    watcher.start()
    time.sleep(0.15)
    # Modify the file
    with open(env_file, "w") as fh:
        fh.write("FOO=changed\nNEW=value\n")
    time.sleep(0.2)
    watcher.stop()
    assert len(received) >= 2
    last = received[-1]
    assert last.get("FOO") == "changed"
    assert last.get("NEW") == "value"


def test_watcher_context_manager(env_file):
    received = []
    with EnvFileWatcher(env_file, callback=received.append, poll_interval=0.05) as w:
        time.sleep(0.2)
    assert len(received) >= 1
    assert not w._thread or not w._thread.is_alive()


def test_watcher_missing_file(tmp_path):
    missing = str(tmp_path / "missing.env")
    received = []
    watcher = EnvFileWatcher(missing, callback=received.append, poll_interval=0.05)
    watcher.start()
    time.sleep(0.15)
    watcher.stop()
    assert received == []


def test_watch_env_file_factory(env_file):
    received = []
    watcher = watch_env_file(env_file, callback=received.append, poll_interval=0.05)
    time.sleep(0.2)
    watcher.stop()
    assert len(received) >= 1


def test_watcher_stop_is_idempotent(env_file):
    received = []
    watcher = EnvFileWatcher(env_file, callback=received.append, poll_interval=0.05)
    watcher.start()
    time.sleep(0.1)
    watcher.stop()
    watcher.stop()  # Should not raise


def test_watcher_start_twice_is_safe(env_file):
    received = []
    watcher = EnvFileWatcher(env_file, callback=received.append, poll_interval=0.05)
    watcher.start()
    watcher.start()  # Should not spawn a second thread
    threads = [t for t in threading.enumerate() if t.name == "envoy-lite-watcher"]
    assert len(threads) == 1
    watcher.stop()
