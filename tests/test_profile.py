"""Tests for envoy_lite.profile module."""

from __future__ import annotations

import pytest
from pathlib import Path

from envoy_lite.profile import ProfileManager, ProfileNotFoundError


@pytest.fixture()
def profiles_dir(tmp_path: Path) -> Path:
    (tmp_path / ".env.dev").write_text("APP_ENV=dev\n")
    (tmp_path / ".env.staging").write_text("APP_ENV=staging\n")
    return tmp_path


def test_available_discovers_files(profiles_dir: Path) -> None:
    mgr = ProfileManager(profiles_dir=str(profiles_dir))
    result = mgr.available()
    assert "dev" in result
    assert "staging" in result


def test_path_for_existing_profile(profiles_dir: Path) -> None:
    mgr = ProfileManager(profiles_dir=str(profiles_dir))
    path = mgr.path_for("dev")
    assert path.exists()
    assert path.name == ".env.dev"


def test_path_for_missing_profile(profiles_dir: Path) -> None:
    mgr = ProfileManager(profiles_dir=str(profiles_dir))
    with pytest.raises(ProfileNotFoundError, match="prod"):
        mgr.path_for("prod")


def test_activate_sets_active(profiles_dir: Path) -> None:
    mgr = ProfileManager(profiles_dir=str(profiles_dir))
    mgr.activate("dev")
    assert mgr.active == "dev"


def test_activate_missing_raises(profiles_dir: Path) -> None:
    mgr = ProfileManager(profiles_dir=str(profiles_dir))
    with pytest.raises(ProfileNotFoundError):
        mgr.activate("nonexistent")


def test_register_custom_path(tmp_path: Path) -> None:
    custom = tmp_path / "custom.env"
    custom.write_text("X=1\n")
    mgr = ProfileManager(profiles_dir=str(tmp_path))
    mgr.register("custom", path=str(custom))
    path = mgr.path_for("custom")
    assert path == custom


def test_active_path_none_before_activate(profiles_dir: Path) -> None:
    mgr = ProfileManager(profiles_dir=str(profiles_dir))
    assert mgr.active is None
    assert mgr.active_path() is None


def test_active_path_after_activate(profiles_dir: Path) -> None:
    mgr = ProfileManager(profiles_dir=str(profiles_dir))
    mgr.activate("staging")
    p = mgr.active_path()
    assert p is not None
    assert p.name == ".env.staging"


def test_available_includes_registered_existing(profiles_dir: Path) -> None:
    mgr = ProfileManager(profiles_dir=str(profiles_dir))
    custom = profiles_dir / ".env.ci"
    custom.write_text("CI=true\n")
    mgr.register("ci")
    result = mgr.available()
    assert "ci" in result


def test_available_excludes_registered_missing(profiles_dir: Path) -> None:
    mgr = ProfileManager(profiles_dir=str(profiles_dir))
    mgr.register("ghost")  # no file created
    result = mgr.available()
    assert "ghost" not in result
