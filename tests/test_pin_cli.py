"""CLI integration tests for the pin command group."""
from __future__ import annotations

import pytest
from pathlib import Path
from click.testing import CliRunner
from envault.cli_pin import pin_group
from envault.pin import set_pin, is_pinned


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> str:
    return str(tmp_path / "test.vault")


def test_pin_set_creates_entry(runner: CliRunner, vault_file: str) -> None:
    result = runner.invoke(
        pin_group,
        ["set", "SECRET", "--vault", vault_file],
        input="abcd1234\nabcd1234\n",
    )
    assert result.exit_code == 0
    assert "PIN set" in result.output
    assert is_pinned(vault_file, "SECRET")


def test_pin_set_mismatched_pins_fails(runner: CliRunner, vault_file: str) -> None:
    result = runner.invoke(
        pin_group,
        ["set", "SECRET", "--vault", vault_file],
        input="abcd1234\nwrongpin\n",
    )
    assert result.exit_code != 0
    assert "do not match" in result.output


def test_pin_set_too_short_fails(runner: CliRunner, vault_file: str) -> None:
    result = runner.invoke(
        pin_group,
        ["set", "SECRET", "--vault", vault_file],
        input="12\n12\n",
    )
    assert result.exit_code != 0


def test_pin_list_shows_pinned_keys(runner: CliRunner, vault_file: str) -> None:
    set_pin(vault_file, "API_KEY", "1234")
    set_pin(vault_file, "DB_PASS", "5678")
    result = runner.invoke(pin_group, ["list", "--vault", vault_file])
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "DB_PASS" in result.output


def test_pin_list_empty(runner: CliRunner, vault_file: str) -> None:
    result = runner.invoke(pin_group, ["list", "--vault", vault_file])
    assert result.exit_code == 0
    assert "No keys" in result.output


def test_pin_remove_existing(runner: CliRunner, vault_file: str) -> None:
    set_pin(vault_file, "KEY", "1234")
    result = runner.invoke(pin_group, ["remove", "KEY", "--vault", vault_file])
    assert result.exit_code == 0
    assert "removed" in result.output
    assert not is_pinned(vault_file, "KEY")


def test_pin_remove_nonexistent(runner: CliRunner, vault_file: str) -> None:
    result = runner.invoke(pin_group, ["remove", "GHOST", "--vault", vault_file])
    assert result.exit_code == 0
    assert "No PIN" in result.output


def test_pin_verify_correct(runner: CliRunner, vault_file: str) -> None:
    set_pin(vault_file, "KEY", "mypin1")
    result = runner.invoke(
        pin_group,
        ["verify", "KEY", "--vault", vault_file],
        input="mypin1\n",
    )
    assert result.exit_code == 0
    assert "correct" in result.output


def test_pin_verify_wrong(runner: CliRunner, vault_file: str) -> None:
    set_pin(vault_file, "KEY", "mypin1")
    result = runner.invoke(
        pin_group,
        ["verify", "KEY", "--vault", vault_file],
        input="badpin\n",
    )
    assert result.exit_code != 0
    assert "Incorrect" in result.output
