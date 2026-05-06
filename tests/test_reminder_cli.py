"""CLI integration tests for reminder commands."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_reminder import reminder_group
from envault.reminder import save_reminders


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    return tmp_path / "test.vault"


def test_set_creates_reminder(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(reminder_group, ["set", "DB_PASS", "30", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert "DB_PASS" in result.output
    assert "30" in result.output


def test_set_invalid_days_fails(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(reminder_group, ["set", "KEY", "0", "--vault", str(vault_file)])
    assert result.exit_code != 0


def test_list_shows_configured_reminders(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(reminder_group, ["set", "API_KEY", "14", "--vault", str(vault_file)])
    result = runner.invoke(reminder_group, ["list", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert "API_KEY" in result.output


def test_list_empty_vault(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(reminder_group, ["list", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert "No reminders" in result.output


def test_remove_existing_reminder(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(reminder_group, ["set", "TOKEN", "7", "--vault", str(vault_file)])
    result = runner.invoke(reminder_group, ["remove", "TOKEN", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_missing_reminder(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(reminder_group, ["remove", "GHOST", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert "No reminder found" in result.output


def test_check_reports_overdue(runner: CliRunner, vault_file: Path) -> None:
    past = datetime.now(timezone.utc) - timedelta(days=60)
    save_reminders(vault_file, {
        "OLD": {"rotate_after_days": 30, "set_at": past.isoformat()},
    })
    result = runner.invoke(reminder_group, ["check", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert "OLD" in result.output
    assert "ago" in result.output


def test_check_all_good(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(reminder_group, ["set", "FRESH", "365", "--vault", str(vault_file)])
    result = runner.invoke(reminder_group, ["check", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert "up to date" in result.output
