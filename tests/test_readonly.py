"""Tests for envault.readonly and envault.cli_readonly."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.readonly import (
    _readonly_path,
    lock_key,
    unlock_key,
    is_locked,
    list_locked,
    load_readonly,
)
from envault.cli_readonly import readonly_group


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "test.vault"


# ---------------------------------------------------------------------------
# Unit tests – readonly module
# ---------------------------------------------------------------------------

def test_sidecar_uses_readonly_suffix(vault_path: Path) -> None:
    assert str(_readonly_path(vault_path)).endswith(".readonly.json")


def test_sidecar_not_created_until_first_lock(vault_path: Path) -> None:
    assert not _readonly_path(vault_path).exists()


def test_load_readonly_returns_empty_when_no_file(vault_path: Path) -> None:
    assert load_readonly(vault_path) == set()


def test_lock_key_persists(vault_path: Path) -> None:
    lock_key(vault_path, "API_KEY")
    assert "API_KEY" in load_readonly(vault_path)


def test_sidecar_is_valid_json(vault_path: Path) -> None:
    lock_key(vault_path, "DB_URL")
    data = json.loads(_readonly_path(vault_path).read_text())
    assert isinstance(data, list)


def test_lock_key_empty_raises(vault_path: Path) -> None:
    with pytest.raises(ValueError):
        lock_key(vault_path, "")


def test_is_locked_returns_true_after_lock(vault_path: Path) -> None:
    lock_key(vault_path, "SECRET")
    assert is_locked(vault_path, "SECRET") is True


def test_is_locked_returns_false_when_not_locked(vault_path: Path) -> None:
    assert is_locked(vault_path, "MISSING") is False


def test_unlock_key_returns_true_when_removed(vault_path: Path) -> None:
    lock_key(vault_path, "TOKEN")
    assert unlock_key(vault_path, "TOKEN") is True
    assert is_locked(vault_path, "TOKEN") is False


def test_unlock_key_returns_false_when_not_locked(vault_path: Path) -> None:
    assert unlock_key(vault_path, "GHOST") is False


def test_list_locked_sorted(vault_path: Path) -> None:
    for k in ["Z_KEY", "A_KEY", "M_KEY"]:
        lock_key(vault_path, k)
    assert list_locked(vault_path) == ["A_KEY", "M_KEY", "Z_KEY"]


def test_list_locked_empty(vault_path: Path) -> None:
    assert list_locked(vault_path) == []


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_lock_creates_entry(runner: CliRunner, vault_path: Path) -> None:
    result = runner.invoke(readonly_group, ["lock", "API_KEY", "--vault", str(vault_path)])
    assert result.exit_code == 0
    assert "Locked" in result.output
    assert is_locked(vault_path, "API_KEY")


def test_cli_unlock_removes_entry(runner: CliRunner, vault_path: Path) -> None:
    lock_key(vault_path, "API_KEY")
    result = runner.invoke(readonly_group, ["unlock", "API_KEY", "--vault", str(vault_path)])
    assert result.exit_code == 0
    assert "Unlocked" in result.output
    assert not is_locked(vault_path, "API_KEY")


def test_cli_unlock_not_locked_message(runner: CliRunner, vault_path: Path) -> None:
    result = runner.invoke(readonly_group, ["unlock", "NOPE", "--vault", str(vault_path)])
    assert result.exit_code == 0
    assert "not locked" in result.output


def test_cli_check_locked(runner: CliRunner, vault_path: Path) -> None:
    lock_key(vault_path, "DB_PASS")
    result = runner.invoke(readonly_group, ["check", "DB_PASS", "--vault", str(vault_path)])
    assert "locked" in result.output


def test_cli_list_shows_keys(runner: CliRunner, vault_path: Path) -> None:
    lock_key(vault_path, "FOO")
    lock_key(vault_path, "BAR")
    result = runner.invoke(readonly_group, ["list", "--vault", str(vault_path)])
    assert "FOO" in result.output
    assert "BAR" in result.output


def test_cli_list_empty_message(runner: CliRunner, vault_path: Path) -> None:
    result = runner.invoke(readonly_group, ["list", "--vault", str(vault_path)])
    assert "No keys" in result.output
