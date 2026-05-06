"""Tests for envault.history module."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.history import (
    load_history,
    save_history,
    record_value,
    get_history,
    clear_history,
    MAX_HISTORY,
    _history_path,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / ".env.vault"


def test_history_file_not_created_until_first_record(vault_path: Path) -> None:
    assert not _history_path(vault_path).exists()


def test_load_history_returns_empty_when_no_file(vault_path: Path) -> None:
    assert load_history(vault_path) == {}


def test_record_value_creates_entry(vault_path: Path) -> None:
    record_value(vault_path, "DB_URL", "ciphertext1", "2024-01-01T00:00:00Z")
    entries = get_history(vault_path, "DB_URL")
    assert len(entries) == 1
    assert entries[0]["ciphertext"] == "ciphertext1"
    assert entries[0]["timestamp"] == "2024-01-01T00:00:00Z"


def test_record_value_appends_multiple_entries(vault_path: Path) -> None:
    for i in range(3):
        record_value(vault_path, "KEY", f"cipher{i}", f"2024-01-0{i+1}T00:00:00Z")
    entries = get_history(vault_path, "KEY")
    assert len(entries) == 3
    assert entries[-1]["ciphertext"] == "cipher2"


def test_record_value_caps_at_max_history(vault_path: Path) -> None:
    for i in range(MAX_HISTORY + 5):
        record_value(vault_path, "KEY", f"cipher{i}", "2024-01-01T00:00:00Z")
    entries = get_history(vault_path, "KEY")
    assert len(entries) == MAX_HISTORY
    assert entries[-1]["ciphertext"] == f"cipher{MAX_HISTORY + 4}"


def test_get_history_returns_empty_for_unknown_key(vault_path: Path) -> None:
    record_value(vault_path, "OTHER", "c", "2024-01-01T00:00:00Z")
    assert get_history(vault_path, "MISSING") == []


def test_clear_history_removes_key(vault_path: Path) -> None:
    record_value(vault_path, "KEY", "c1", "2024-01-01T00:00:00Z")
    record_value(vault_path, "OTHER", "c2", "2024-01-01T00:00:00Z")
    clear_history(vault_path, "KEY")
    assert get_history(vault_path, "KEY") == []
    assert len(get_history(vault_path, "OTHER")) == 1


def test_clear_history_no_error_when_key_missing(vault_path: Path) -> None:
    clear_history(vault_path, "NONEXISTENT")  # should not raise


def test_history_file_is_valid_json(vault_path: Path) -> None:
    record_value(vault_path, "K", "v", "2024-01-01T00:00:00Z")
    raw = _history_path(vault_path).read_text(encoding="utf-8")
    data = json.loads(raw)
    assert "K" in data
