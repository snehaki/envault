"""CLI integration tests for the 'dep' command group."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_dependency import dependency_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path):
    return str(tmp_path / "test.vault")


def _run(runner, vault_file, *args):
    return runner.invoke(
        dependency_group, [*args, "--vault", vault_file], catch_exceptions=False
    )


def test_dep_set_creates_entry(runner, vault_file):
    result = _run(runner, vault_file, "set", "DB_URL", "DB_HOST", "DB_PORT")
    assert result.exit_code == 0
    assert "DB_URL" in result.output
    assert "DB_HOST" in result.output


def test_dep_list_shows_entries(runner, vault_file):
    _run(runner, vault_file, "set", "A", "B")
    result = _run(runner, vault_file, "list")
    assert result.exit_code == 0
    assert "A" in result.output
    assert "B" in result.output


def test_dep_list_empty(runner, vault_file):
    result = _run(runner, vault_file, "list")
    assert result.exit_code == 0
    assert "No dependencies" in result.output


def test_dep_remove_existing(runner, vault_file):
    _run(runner, vault_file, "set", "X", "Y")
    result = _run(runner, vault_file, "remove", "X")
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_dep_remove_missing(runner, vault_file):
    result = _run(runner, vault_file, "remove", "GHOST")
    assert result.exit_code == 0
    assert "No dependency entry" in result.output


def test_dep_remove_clears_from_list(runner, vault_file):
    """After removing a key, it should no longer appear in 'list' output."""
    _run(runner, vault_file, "set", "X", "Y")
    _run(runner, vault_file, "remove", "X")
    result = _run(runner, vault_file, "list")
    assert result.exit_code == 0
    assert "X" not in result.output


def test_dep_dependents_shows_reverse(runner, vault_file):
    _run(runner, vault_file, "set", "APP", "HOST")
    result = _run(runner, vault_file, "dependents", "HOST")
    assert result.exit_code == 0
    assert "APP" in result.output


def test_dep_dependents_none(runner, vault_file):
    result = _run(runner, vault_file, "dependents", "ORPHAN")
    assert result.exit_code == 0
    assert "No keys depend on" in result.output


def test_dep_order_respects_deps(runner, vault_file):
    _run(runner, vault_file, "set", "C", "B")
    _run(runner, vault_file, "set", "B", "A")
    result = _run(runner, vault_file, "order", "C", "B", "A")
    assert result.exit_code == 0
    lines = [l for l in result.output.splitlines() if l.strip()]
    assert lines.index("A") < lines.index("B") < lines.index("C")


def test_dep_self_reference_fails(runner, vault_file):
    result = runner.invoke(
        dependency_group, ["set", "A", "A", "--vault", vault_file]
    )
    assert result.exit_code != 0
