"""Tests for envault.search module."""

import pytest

from envault.crypto import encrypt
from envault.search import filter_by_prefix, search_keys

PASS = "hunter2"


def _make_vault(*pairs: tuple[str, str]) -> dict:
    """Build a minimal vault dict from (key, plaintext) pairs."""
    entries = {key: encrypt(value, PASS) for key, value in pairs}
    return {"entries": entries}


# ---------------------------------------------------------------------------
# search_keys — key matching
# ---------------------------------------------------------------------------

def test_search_keys_glob_exact_match():
    vault = _make_vault(("DATABASE_URL", "postgres://localhost/db"), ("SECRET_KEY", "abc"))
    results = search_keys(vault, PASS, "DATABASE_URL")
    assert len(results) == 1
    assert results[0]["key"] == "DATABASE_URL"


def test_search_keys_glob_wildcard():
    vault = _make_vault(("DB_HOST", "localhost"), ("DB_PORT", "5432"), ("SECRET", "x"))
    results = search_keys(vault, PASS, "DB_*")
    keys = [r["key"] for r in results]
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys
    assert "SECRET" not in keys


def test_search_keys_no_match_returns_empty():
    vault = _make_vault(("FOO", "bar"))
    results = search_keys(vault, PASS, "MISSING_*")
    assert results == []


def test_search_keys_results_are_sorted():
    vault = _make_vault(("Z_KEY", "1"), ("A_KEY", "2"), ("M_KEY", "3"))
    results = search_keys(vault, PASS, "*_KEY")
    keys = [r["key"] for r in results]
    assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# search_keys — value matching
# ---------------------------------------------------------------------------

def test_search_keys_value_match_returns_decrypted_value():
    vault = _make_vault(("API_URL", "https://example.com"), ("OTHER", "nope"))
    results = search_keys(vault, PASS, "*example*", search_values=True)
    assert len(results) == 1
    assert results[0]["key"] == "API_URL"
    assert results[0]["value"] == "https://example.com"


def test_search_keys_value_search_includes_value_field():
    vault = _make_vault(("TOKEN", "secret-token-value"))
    results = search_keys(vault, PASS, "TOKEN", search_values=True)
    assert "value" in results[0]


def test_search_keys_without_value_search_omits_value_field():
    vault = _make_vault(("TOKEN", "secret-token-value"))
    results = search_keys(vault, PASS, "TOKEN", search_values=False)
    assert "value" not in results[0]


# ---------------------------------------------------------------------------
# search_keys — regex mode
# ---------------------------------------------------------------------------

def test_search_keys_regex_mode():
    vault = _make_vault(("DB_HOST", "h"), ("DB_PORT", "p"), ("SECRET", "s"))
    results = search_keys(vault, PASS, r"^DB_", regex=True)
    keys = [r["key"] for r in results]
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys
    assert "SECRET" not in keys


# ---------------------------------------------------------------------------
# filter_by_prefix
# ---------------------------------------------------------------------------

def test_filter_by_prefix_returns_matching_keys():
    vault = _make_vault(("AWS_KEY", "k"), ("AWS_SECRET", "s"), ("GCP_KEY", "g"))
    result = filter_by_prefix(vault, "AWS_")
    assert result == ["AWS_KEY", "AWS_SECRET"]


def test_filter_by_prefix_empty_when_no_match():
    vault = _make_vault(("FOO", "bar"))
    assert filter_by_prefix(vault, "MISSING_") == []


def test_filter_by_prefix_sorted():
    vault = _make_vault(("Z_VAR", "1"), ("A_VAR", "2"), ("M_VAR", "3"))
    result = filter_by_prefix(vault, "")
    assert result == sorted(result)
