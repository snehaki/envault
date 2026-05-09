"""Tests for envault.retention module."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envault.retention import (
    _retention_path,
    expired_keys,
    load_retention,
    remove_retention,
    set_retention,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.vault")


def test_sidecar_uses_retention_suffix(vault_path: str) -> None:
    assert str(_retention_path(vault_path)).endswith(".retention.json")


def test_sidecar_not_created_until_first_set(vault_path: str) -> None:
    assert not _retention_path(vault_path).exists()


def test_load_retention_returns_empty_when_no_file(vault_path: str) -> None:
    assert load_retention(vault_path) == {}


def test_set_retention_persists(vault_path: str) -> None:
    set_retention(vault_path, "API_KEY", 30)
    assert load_retention(vault_path)["API_KEY"] == 30


def test_set_retention_sidecar_is_valid_json(vault_path: str) -> None:
    set_retention(vault_path, "DB_PASS", 7)
    raw = _retention_path(vault_path).read_text()
    parsed = json.loads(raw)
    assert parsed["DB_PASS"] == 7


def test_set_retention_raises_for_non_positive_days(vault_path: str) -> None:
    with pytest.raises(ValueError):
        set_retention(vault_path, "KEY", 0)
    with pytest.raises(ValueError):
        set_retention(vault_path, "KEY", -5)


def test_set_retention_overwrites_existing(vault_path: str) -> None:
    set_retention(vault_path, "TOKEN", 10)
    set_retention(vault_path, "TOKEN", 60)
    assert load_retention(vault_path)["TOKEN"] == 60


def test_remove_retention_returns_true_when_removed(vault_path: str) -> None:
    set_retention(vault_path, "SECRET", 14)
    assert remove_retention(vault_path, "SECRET") is True
    assert "SECRET" not in load_retention(vault_path)


def test_remove_retention_returns_false_when_missing(vault_path: str) -> None:
    assert remove_retention(vault_path, "GHOST") is False


def test_expired_keys_detects_stale_key(vault_path: str) -> None:
    set_retention(vault_path, "OLD_KEY", 30)
    last_accessed = {
        "OLD_KEY": datetime.now(timezone.utc) - timedelta(days=31),
    }
    assert "OLD_KEY" in expired_keys(vault_path, last_accessed)


def test_expired_keys_ignores_fresh_key(vault_path: str) -> None:
    set_retention(vault_path, "FRESH_KEY", 30)
    last_accessed = {
        "FRESH_KEY": datetime.now(timezone.utc) - timedelta(days=5),
    }
    assert expired_keys(vault_path, last_accessed) == []


def test_expired_keys_treats_unaccessed_as_epoch(vault_path: str) -> None:
    set_retention(vault_path, "NEVER_USED", 1)
    # No entry in last_accessed -> treated as epoch -> definitely expired
    result = expired_keys(vault_path, {})
    assert "NEVER_USED" in result


def test_expired_keys_returns_sorted(vault_path: str) -> None:
    for key in ("ZEBRA", "ALPHA", "MANGO"):
        set_retention(vault_path, key, 1)
    old = datetime(1980, 1, 1, tzinfo=timezone.utc)
    last_accessed = {"ZEBRA": old, "ALPHA": old, "MANGO": old}
    result = expired_keys(vault_path, last_accessed)
    assert result == sorted(result)
