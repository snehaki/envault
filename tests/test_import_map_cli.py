"""CLI integration tests for the import-map commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_import_map import map_group
from envault.import_map import load_map


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    return tmp_path / "test.vault"


def _run_set(runner: CliRunner, vault_file: Path, src: str, tgt: str):
    return runner.invoke(
        map_group,
        ["set", src, tgt, "--vault", str(vault_file)],
    )


def test_map_set_creates_entry(
    runner: CliRunner, vault_file: Path
) -> None:
    result = _run_set(runner, vault_file, "DB_HOST", "DATABASE_HOST")
    assert result.exit_code == 0
    assert "DB_HOST" in result.output
    assert "DATABASE_HOST" in result.output
    assert load_map(vault_file)["DB_HOST"] == "DATABASE_HOST"


def test_map_list_shows_entries(
    runner: CliRunner, vault_file: Path
) -> None:
    _run_set(runner, vault_file, "A", "B")
    _run_set(runner, vault_file, "C", "D")
    result = runner.invoke(
        map_group, ["list", "--vault", str(vault_file)]
    )
    assert result.exit_code == 0
    assert "A" in result.output
    assert "B" in result.output
    assert "C" in result.output


def test_map_list_empty(
    runner: CliRunner, vault_file: Path
) -> None:
    result = runner.invoke(
        map_group, ["list", "--vault", str(vault_file)]
    )
    assert result.exit_code == 0
    assert "No import-map" in result.output


def test_map_remove_existing(
    runner: CliRunner, vault_file: Path
) -> None:
    _run_set(runner, vault_file, "OLD", "NEW")
    result = runner.invoke(
        map_group, ["remove", "OLD", "--vault", str(vault_file)]
    )
    assert result.exit_code == 0
    assert "Removed" in result.output
    assert "OLD" not in load_map(vault_file)


def test_map_remove_missing(
    runner: CliRunner, vault_file: Path
) -> None:
    result = runner.invoke(
        map_group, ["remove", "GHOST", "--vault", str(vault_file)]
    )
    assert result.exit_code == 0
    assert "No mapping found" in result.output
