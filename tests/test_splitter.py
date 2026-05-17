"""Tests for envoy_lite.splitter."""
from __future__ import annotations

import json
import os

import pytest

from envoy_lite.splitter import (
    SplitError,
    split_by_predicate,
    split_by_prefix,
    write_splits,
)


SAMPLE = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "AWS_KEY": "AKID",
    "AWS_SECRET": "secret",
    "APP_DEBUG": "true",
    "STANDALONE": "yes",
}


# ---------------------------------------------------------------------------
# split_by_prefix
# ---------------------------------------------------------------------------

def test_split_by_prefix_basic():
    result = split_by_prefix(SAMPLE, ["DB_", "AWS_"])
    assert result["DB_"] == {"DB_HOST": "localhost", "DB_PORT": "5432"}
    assert result["AWS_"] == {"AWS_KEY": "AKID", "AWS_SECRET": "secret"}


def test_split_by_prefix_unmatched_included_by_default():
    result = split_by_prefix(SAMPLE, ["DB_", "AWS_"])
    assert "APP_DEBUG" in result["__unmatched__"]
    assert "STANDALONE" in result["__unmatched__"]


def test_split_by_prefix_unmatched_excluded():
    result = split_by_prefix(SAMPLE, ["DB_"], include_unmatched=False)
    assert "__unmatched__" not in result


def test_split_by_prefix_strip_prefix():
    result = split_by_prefix(SAMPLE, ["DB_"], strip_prefix=True)
    assert "HOST" in result["DB_"]
    assert "PORT" in result["DB_"]
    assert "DB_HOST" not in result["DB_"]


def test_split_by_prefix_first_match_wins():
    env = {"DB_HOST": "h", "DB_HOST_EXTRA": "e"}
    # Both start with "DB_"; "DB_HOST" prefix is listed first
    result = split_by_prefix(env, ["DB_HOST", "DB_"])
    assert "DB_HOST" in result["DB_HOST"]
    assert "DB_HOST_EXTRA" in result["DB_HOST"]
    assert result["DB_"] == {}


def test_split_by_prefix_empty_prefixes_raises():
    with pytest.raises(SplitError, match="prefixes list must not be empty"):
        split_by_prefix(SAMPLE, [])


def test_split_by_prefix_empty_env():
    result = split_by_prefix({}, ["DB_"])
    assert result["DB_"] == {}
    assert result["__unmatched__"] == {}


# ---------------------------------------------------------------------------
# split_by_predicate
# ---------------------------------------------------------------------------

def test_split_by_predicate_basic():
    def bucket(k, v):
        return "secrets" if "SECRET" in k or "KEY" in k else "config"

    result = split_by_predicate(SAMPLE, bucket)
    assert "AWS_KEY" in result["secrets"]
    assert "AWS_SECRET" in result["secrets"]
    assert "DB_HOST" in result["config"]


def test_split_by_predicate_empty_env():
    result = split_by_predicate({}, lambda k, v: "all")
    assert result == {}


def test_split_by_predicate_single_bucket():
    result = split_by_predicate({"A": "1", "B": "2"}, lambda k, v: "only")
    assert set(result["only"].keys()) == {"A", "B"}


# ---------------------------------------------------------------------------
# write_splits
# ---------------------------------------------------------------------------

def test_write_splits_dotenv(tmp_path):
    buckets = {"db": {"HOST": "localhost"}, "aws": {"KEY": "AKID"}}
    paths = write_splits(buckets, str(tmp_path), fmt="dotenv")
    assert len(paths) == 2
    contents = {os.path.basename(p): open(p).read() for p in paths}
    assert "HOST=localhost\n" in contents["db.env"]
    assert "KEY=AKID\n" in contents["aws.env"]


def test_write_splits_json(tmp_path):
    buckets = {"db": {"HOST": "localhost"}}
    paths = write_splits(buckets, str(tmp_path), fmt="json")
    assert paths[0].endswith(".json")
    data = json.loads(open(paths[0]).read())
    assert data == {"HOST": "localhost"}


def test_write_splits_creates_output_dir(tmp_path):
    out = str(tmp_path / "nested" / "dir")
    write_splits({"x": {"K": "V"}}, out)
    assert os.path.isdir(out)


def test_write_splits_unsupported_format_raises(tmp_path):
    with pytest.raises(SplitError, match="unsupported format"):
        write_splits({"x": {}}, str(tmp_path), fmt="yaml")


def test_write_splits_unmatched_bucket_safe_name(tmp_path):
    buckets = {"__unmatched__": {"LONE": "1"}}
    paths = write_splits(buckets, str(tmp_path), fmt="dotenv")
    assert any("unmatched" in os.path.basename(p) for p in paths)
