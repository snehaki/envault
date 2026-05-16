"""Tests for envault.comment module."""

from __future__ import annotations

import json

import pytest

from envault.comment import (
    _comments_path,
    all_comments,
    get_comment,
    load_comments,
    remove_comment,
    set_comment,
)


@pytest.fixture()
def vault_path(tmp_path) -> str:
    return str(tmp_path / "test.vault")


def test_sidecar_uses_comments_suffix(vault_path):
    p = _comments_path(vault_path)
    assert p.name.endswith(".comments.json")


def test_sidecar_not_created_until_first_set(vault_path):
    p = _comments_path(vault_path)
    assert not p.exists()
    load_comments(vault_path)  # read-only, should not create
    assert not p.exists()


def test_sidecar_created_after_set(vault_path):
    set_comment(vault_path, "API_KEY", "Main API key")
    assert _comments_path(vault_path).exists()


def test_sidecar_is_valid_json(vault_path):
    set_comment(vault_path, "DB_URL", "Primary database")
    raw = _comments_path(vault_path).read_text()
    data = json.loads(raw)
    assert isinstance(data, dict)


def test_load_comments_returns_empty_when_no_file(vault_path):
    assert load_comments(vault_path) == {}


def test_set_comment_persists(vault_path):
    set_comment(vault_path, "SECRET", "Top secret value")
    assert load_comments(vault_path)["SECRET"] == "Top secret value"


def test_set_comment_overwrites_existing(vault_path):
    set_comment(vault_path, "KEY", "first")
    set_comment(vault_path, "KEY", "second")
    assert get_comment(vault_path, "KEY") == "second"


def test_set_comment_empty_key_raises(vault_path):
    with pytest.raises(ValueError, match="key"):
        set_comment(vault_path, "", "some comment")


def test_set_comment_empty_comment_raises(vault_path):
    with pytest.raises(ValueError, match="comment"):
        set_comment(vault_path, "KEY", "")


def test_get_comment_returns_none_when_not_set(vault_path):
    assert get_comment(vault_path, "MISSING") is None


def test_remove_comment_returns_true_when_removed(vault_path):
    set_comment(vault_path, "FOO", "bar")
    assert remove_comment(vault_path, "FOO") is True
    assert get_comment(vault_path, "FOO") is None


def test_remove_comment_returns_false_when_absent(vault_path):
    assert remove_comment(vault_path, "NONEXISTENT") is False


def test_all_comments_returns_all_entries(vault_path):
    set_comment(vault_path, "A", "alpha")
    set_comment(vault_path, "B", "beta")
    result = all_comments(vault_path)
    assert result == {"A": "alpha", "B": "beta"}


def test_multiple_keys_independent(vault_path):
    set_comment(vault_path, "X", "ex")
    set_comment(vault_path, "Y", "why")
    remove_comment(vault_path, "X")
    assert get_comment(vault_path, "Y") == "why"
    assert get_comment(vault_path, "X") is None
