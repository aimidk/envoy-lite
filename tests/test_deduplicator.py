"""Tests for envoy_lite.deduplicator."""

import pytest

from envoy_lite.deduplicator import (
    DeduplicateError,
    deduplicate,
    find_duplicates,
)


# ---------------------------------------------------------------------------
# deduplicate – strategy='last' (default)
# ---------------------------------------------------------------------------

def test_deduplicate_no_duplicates_returns_all():
    pairs = [("A", "1"), ("B", "2"), ("C", "3")]
    assert deduplicate(pairs) == {"A": "1", "B": "2", "C": "3"}


def test_deduplicate_last_keeps_final_value():
    pairs = [("A", "1"), ("B", "2"), ("A", "99")]
    result = deduplicate(pairs, strategy="last")
    assert result["A"] == "99"


def test_deduplicate_last_preserves_other_keys():
    pairs = [("A", "1"), ("B", "2"), ("A", "99")]
    result = deduplicate(pairs, strategy="last")
    assert result["B"] == "2"
    assert len(result) == 2


def test_deduplicate_default_is_last():
    pairs = [("X", "old"), ("X", "new")]
    assert deduplicate(pairs)["X"] == "new"


# ---------------------------------------------------------------------------
# deduplicate – strategy='first'
# ---------------------------------------------------------------------------

def test_deduplicate_first_keeps_initial_value():
    pairs = [("A", "1"), ("A", "99")]
    result = deduplicate(pairs, strategy="first")
    assert result["A"] == "1"


def test_deduplicate_first_length_correct():
    pairs = [("A", "1"), ("B", "2"), ("A", "3"), ("B", "4")]
    result = deduplicate(pairs, strategy="first")
    assert len(result) == 2
    assert result == {"A": "1", "B": "2"}


# ---------------------------------------------------------------------------
# deduplicate – strategy='error'
# ---------------------------------------------------------------------------

def test_deduplicate_error_raises_on_duplicate():
    pairs = [("A", "1"), ("B", "2"), ("A", "3")]
    with pytest.raises(DeduplicateError, match="A"):
        deduplicate(pairs, strategy="error")


def test_deduplicate_error_no_duplicate_passes():
    pairs = [("A", "1"), ("B", "2")]
    result = deduplicate(pairs, strategy="error")
    assert result == {"A": "1", "B": "2"}


# ---------------------------------------------------------------------------
# deduplicate – invalid strategy
# ---------------------------------------------------------------------------

def test_deduplicate_unknown_strategy_raises():
    with pytest.raises(ValueError, match="Unknown strategy"):
        deduplicate([("A", "1")], strategy="random")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# find_duplicates
# ---------------------------------------------------------------------------

def test_find_duplicates_none():
    pairs = [("A", "1"), ("B", "2")]
    assert find_duplicates(pairs) == {}


def test_find_duplicates_single_key():
    pairs = [("A", "1"), ("B", "2"), ("A", "3")]
    result = find_duplicates(pairs)
    assert result == {"A": [0, 2]}


def test_find_duplicates_multiple_keys():
    pairs = [("A", "1"), ("B", "2"), ("A", "3"), ("B", "4"), ("C", "5")]
    result = find_duplicates(pairs)
    assert set(result.keys()) == {"A", "B"}
    assert result["A"] == [0, 2]
    assert result["B"] == [1, 3]
    assert "C" not in result


def test_find_duplicates_three_occurrences():
    pairs = [("X", "a"), ("X", "b"), ("X", "c")]
    result = find_duplicates(pairs)
    assert result["X"] == [0, 1, 2]


def test_find_duplicates_empty_input():
    assert find_duplicates([]) == {}
