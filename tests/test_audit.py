"""Tests for envault.audit."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault import audit


def test_record_creates_audit_file(tmp_path: Path) -> None:
    vault_path = tmp_path / ".envault"
    audit.record(vault_path, "set", "MY_KEY")
    audit_path = vault_path.with_suffix(".audit.jsonl")
    assert audit_path.exists()


def test_record_appends_entries(tmp_path: Path) -> None:
    vault_path = tmp_path / ".envault"
    audit.record(vault_path, "set", "A")
    audit.record(vault_path, "get", "A")
    entries = audit.read_log(vault_path)
    assert len(entries) == 2
    assert entries[0]["action"] == "set"
    assert entries[1]["action"] == "get"


def test_record_entry_has_timestamp(tmp_path: Path) -> None:
    vault_path = tmp_path / ".envault"
    audit.record(vault_path, "export")
    entries = audit.read_log(vault_path)
    assert "ts" in entries[0]
    assert entries[0]["ts"].endswith("+00:00")


def test_record_without_key_omits_key_field(tmp_path: Path) -> None:
    vault_path = tmp_path / ".envault"
    audit.record(vault_path, "export")
    entries = audit.read_log(vault_path)
    assert "key" not in entries[0]


def test_read_log_returns_empty_list_when_no_file(tmp_path: Path) -> None:
    vault_path = tmp_path / ".envault"
    entries = audit.read_log(vault_path)
    assert entries == []


def test_format_log_no_entries() -> None:
    result = audit.format_log([])
    assert "No audit" in result


def test_format_log_shows_action_and_key(tmp_path: Path) -> None:
    vault_path = tmp_path / ".envault"
    audit.record(vault_path, "set", "SECRET_KEY")
    entries = audit.read_log(vault_path)
    formatted = audit.format_log(entries)
    assert "set" in formatted
    assert "SECRET_KEY" in formatted
