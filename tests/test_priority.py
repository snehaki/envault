"""Tests for envault.priority module."""

from __future__ import annotations

import json

import pytest

from envault.priority import (
    DEFAULT_PRIORITY,
    _priority_path,
    get_priority,
    keys_by_priority,
    load_priorities,
    remove_priority,
    set_priority,
)


@pytest.fixture()
def vault_path(tmp_path):
    return tmp_path / "test.vault"


# ---------------------------------------------------------------------------
# sidecar file behaviour
# ---------------------------------------------------------------------------

def test_sidecar_uses_priorities_suffix(vault_path):
    assert _priority_path(vault_path).name == "test.priorities.json"


def test_sidecar_not_created_until_first_set(vault_path):
    assert not _priority_path(vault_path).exists()


def test_sidecar_created_after_set(vault_path):
    set_priority(vault_path, "API_KEY", "high")
    assert _priority_path(vault_path).exists()


def test_sidecar_is_valid_json(vault_path):
    set_priority(vault_path, "DB_PASS", "critical")
    data = json.loads(_priority_path(vault_path).read_text())
    assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# load / save
# ---------------------------------------------------------------------------

def test_load_priorities_returns_empty_when_no_file(vault_path):
    assert load_priorities(vault_path) == {}


def test_set_priority_persists(vault_path):
    set_priority(vault_path, "SECRET", "high")
    assert load_priorities(vault_path)["SECRET"] == "high"


def test_set_priority_overwrites_existing(vault_path):
    set_priority(vault_path, "TOKEN", "low")
    set_priority(vault_path, "TOKEN", "critical")
    assert load_priorities(vault_path)["TOKEN"] == "critical"


def test_set_priority_case_insensitive(vault_path):
    set_priority(vault_path, "X", "HIGH")
    assert load_priorities(vault_path)["X"] == "high"


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------

def test_set_priority_empty_key_raises(vault_path):
    with pytest.raises(ValueError, match="empty"):
        set_priority(vault_path, "", "low")


def test_set_priority_unknown_level_raises(vault_path):
    with pytest.raises(ValueError, match="Invalid priority"):
        set_priority(vault_path, "KEY", "urgent")


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------

def test_remove_priority_returns_true_when_removed(vault_path):
    set_priority(vault_path, "KEY", "low")
    assert remove_priority(vault_path, "KEY") is True


def test_remove_priority_returns_false_when_missing(vault_path):
    assert remove_priority(vault_path, "GHOST") is False


def test_remove_priority_deletes_entry(vault_path):
    set_priority(vault_path, "KEY", "medium")
    remove_priority(vault_path, "KEY")
    assert "KEY" not in load_priorities(vault_path)


# ---------------------------------------------------------------------------
# get / keys_by_priority
# ---------------------------------------------------------------------------

def test_get_priority_returns_default_when_unset(vault_path):
    assert get_priority(vault_path, "UNSET") == DEFAULT_PRIORITY


def test_get_priority_returns_set_level(vault_path):
    set_priority(vault_path, "DB_URL", "critical")
    assert get_priority(vault_path, "DB_URL") == "critical"


def test_keys_by_priority_returns_sorted_list(vault_path):
    set_priority(vault_path, "Z_KEY", "high")
    set_priority(vault_path, "A_KEY", "high")
    set_priority(vault_path, "M_KEY", "low")
    assert keys_by_priority(vault_path, "high") == ["A_KEY", "Z_KEY"]


def test_keys_by_priority_empty_when_none_match(vault_path):
    set_priority(vault_path, "KEY", "low")
    assert keys_by_priority(vault_path, "critical") == []
