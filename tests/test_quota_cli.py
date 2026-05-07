"""CLI integration tests for quota commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_quota import quota_group
from envault.quota import _DEFAULT_LIMIT, get_limit


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.vault"
    p.write_text("{}")
    return p


def test_quota_set_creates_sidecar(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(quota_group, ["set", "25", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert "25" in result.output
    assert get_limit(vault_file) == 25


def test_quota_show_displays_default(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(quota_group, ["show", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert str(_DEFAULT_LIMIT) in result.output


def test_quota_show_displays_set_value(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(quota_group, ["set", "42", "--vault", str(vault_file)])
    result = runner.invoke(quota_group, ["show", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert "42" in result.output


def test_quota_remove_existing(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(quota_group, ["set", "10", "--vault", str(vault_file)])
    result = runner.invoke(quota_group, ["remove", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert "removed" in result.output.lower()
    assert get_limit(vault_file) == _DEFAULT_LIMIT


def test_quota_remove_when_not_set(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(quota_group, ["remove", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert "no quota" in result.output.lower()


def test_quota_set_invalid_limit_fails(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(quota_group, ["set", "0", "--vault", str(vault_file)])
    assert result.exit_code != 0
