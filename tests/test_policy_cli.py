"""CLI integration tests for policy commands."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_policy import policy_group
from envault.crypto import encrypt
from envault.vault import save_vault

PASSPHRASE = "testpass"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> str:
    path = str(tmp_path / "test.vault")
    vault_data = {
        "secrets": {
            "DB_PASSWORD": encrypt("supersecret", PASSPHRASE),
            "API_KEY": encrypt("abc", PASSPHRASE),
        }
    }
    save_vault(path, vault_data)
    return path


def test_policy_set_creates_entry(runner: CliRunner, vault_file: str) -> None:
    result = runner.invoke(
        policy_group, ["set", "DB_PASSWORD", "min_length", "8", "--vault", vault_file]
    )
    assert result.exit_code == 0
    assert "min_length=8" in result.output


def test_policy_list_shows_rules(runner: CliRunner, vault_file: str) -> None:
    runner.invoke(policy_group, ["set", "API_KEY", "required", "true", "--vault", vault_file])
    result = runner.invoke(policy_group, ["list", "--vault", vault_file])
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "required" in result.output


def test_policy_list_empty(runner: CliRunner, vault_file: str) -> None:
    result = runner.invoke(policy_group, ["list", "--vault", vault_file])
    assert result.exit_code == 0
    assert "No policies" in result.output


def test_policy_remove(runner: CliRunner, vault_file: str) -> None:
    runner.invoke(policy_group, ["set", "DB_PASSWORD", "required", "true", "--vault", vault_file])
    result = runner.invoke(policy_group, ["remove", "DB_PASSWORD", "--vault", vault_file])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_policy_check_passes(runner: CliRunner, vault_file: str) -> None:
    runner.invoke(policy_group, ["set", "DB_PASSWORD", "min_length", "5", "--vault", vault_file])
    result = runner.invoke(
        policy_group, ["check", "--vault", vault_file, "--passphrase", PASSPHRASE]
    )
    assert result.exit_code == 0
    assert "passed" in result.output


def test_policy_check_fails_on_violation(runner: CliRunner, vault_file: str) -> None:
    runner.invoke(
        policy_group, ["set", "API_KEY", "min_length", "20", "--vault", vault_file]
    )
    result = runner.invoke(
        policy_group, ["check", "--vault", vault_file, "--passphrase", PASSPHRASE]
    )
    assert result.exit_code != 0
    assert "FAIL" in result.output
