"""Tests for envault.access_log."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from envault.access_log import (
    _access_log_path,
    clear_access_log,
    get_key_history,
    load_access_log,
    record_access,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    p = tmp_path / "test.vault"
    p.write_text("{}", encoding="utf-8")
    return p


def test_sidecar_uses_access_log_suffix(vault_path: Path) -> None:
    assert _access_log_path(vault_path).name == "test.access_log.json"


def test_sidecar_not_created_until_first_record(vault_path: Path) -> None:
    assert not _access_log_path(vault_path).exists()


def test_load_access_log_returns_empty_when_no_file(vault_path: Path) -> None:
    assert load_access_log(vault_path) == []


def test_record_access_creates_sidecar(vault_path: Path) -> None:
    record_access(vault_path, "get", "MY_KEY")
    assert _access_log_path(vault_path).exists()


def test_record_access_entry_fields(vault_path: Path) -> None:
    record_access(vault_path, "set", "DB_URL", actor="alice")
    entries = load_access_log(vault_path)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["operation"] == "set"
    assert entry["key"] == "DB_URL"
    assert entry["actor"] == "alice"
    assert "timestamp" in entry


def test_record_access_without_actor_omits_actor_field(vault_path: Path) -> None:
    record_access(vault_path, "delete", "OLD_KEY")
    entry = load_access_log(vault_path)[0]
    assert "actor" not in entry


def test_record_access_appends_multiple_entries(vault_path: Path) -> None:
    record_access(vault_path, "set", "A")
    record_access(vault_path, "get", "A")
    record_access(vault_path, "delete", "A")
    assert len(load_access_log(vault_path)) == 3


def test_record_access_invalid_operation_raises(vault_path: Path) -> None:
    with pytest.raises(ValueError, match="operation must be one of"):
        record_access(vault_path, "read", "KEY")


def test_record_access_empty_key_raises(vault_path: Path) -> None:
    with pytest.raises(ValueError, match="key must not be empty"):
        record_access(vault_path, "get", "")


def test_get_key_history_filters_by_key(vault_path: Path) -> None:
    record_access(vault_path, "set", "A")
    record_access(vault_path, "set", "B")
    record_access(vault_path, "get", "A")
    history = get_key_history(vault_path, "A")
    assert len(history) == 2
    assert all(e["key"] == "A" for e in history)


def test_get_key_history_returns_empty_for_unknown_key(vault_path: Path) -> None:
    record_access(vault_path, "set", "A")
    assert get_key_history(vault_path, "MISSING") == []


def test_clear_access_log_removes_sidecar(vault_path: Path) -> None:
    record_access(vault_path, "get", "X")
    assert _access_log_path(vault_path).exists()
    clear_access_log(vault_path)
    assert not _access_log_path(vault_path).exists()


def test_clear_access_log_noop_when_no_file(vault_path: Path) -> None:
    # Should not raise even when file does not exist
    clear_access_log(vault_path)


def test_sidecar_is_valid_json(vault_path: Path) -> None:
    record_access(vault_path, "set", "KEY", actor="ci")
    raw = _access_log_path(vault_path).read_text(encoding="utf-8")
    data = json.loads(raw)
    assert isinstance(data, list)
