"""Integration tests for the history CLI commands."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_history import history_group
from envault.history import record_value
from envault.crypto import encrypt

PASS = "test-pass"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    return tmp_path / ".env.vault"


def test_history_show_no_entries(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(history_group, ["show", "DB_URL", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert "No history found" in result.output


def test_history_show_lists_entries(runner: CliRunner, vault_file: Path) -> None:
    record_value(vault_file, "API_KEY", "cipher1", "2024-06-01T10:00:00Z")
    record_value(vault_file, "API_KEY", "cipher2", "2024-06-02T10:00:00Z")
    result = runner.invoke(history_group, ["show", "API_KEY", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert "2 entries" in result.output
    assert "2024-06-01" in result.output
    assert "2024-06-02" in result.output


def test_history_show_decrypt_values(runner: CliRunner, vault_file: Path) -> None:
    ciphertext = encrypt("supersecret", PASS)
    record_value(vault_file, "SECRET", ciphertext, "2024-06-01T00:00:00Z")
    result = runner.invoke(
        history_group,
        ["show", "SECRET", "--vault", str(vault_file), "--decrypt-values"],
        input=f"{PASS}\n",
    )
    assert result.exit_code == 0
    assert "supersecret" in result.output


def test_history_clear_removes_entries(runner: CliRunner, vault_file: Path) -> None:
    record_value(vault_file, "DB_PASS", "c1", "2024-06-01T00:00:00Z")
    result = runner.invoke(
        history_group,
        ["clear", "DB_PASS", "--vault", str(vault_file)],
        input="y\n",
    )
    assert result.exit_code == 0
    assert "cleared" in result.output

    result2 = runner.invoke(history_group, ["show", "DB_PASS", "--vault", str(vault_file)])
    assert "No history found" in result2.output


def test_history_clear_aborted_keeps_entries(runner: CliRunner, vault_file: Path) -> None:
    record_value(vault_file, "KEY", "c1", "2024-06-01T00:00:00Z")
    result = runner.invoke(
        history_group,
        ["clear", "KEY", "--vault", str(vault_file)],
        input="n\n",
    )
    assert result.exit_code != 0 or "Aborted" in result.output
    from envault.history import get_history
    assert len(get_history(vault_file, "KEY")) == 1
