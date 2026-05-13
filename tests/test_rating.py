"""Tests for envault.rating and envault.cli_rating."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.rating import (
    get_rating,
    keys_by_rating,
    load_ratings,
    remove_rating,
    set_rating,
    top_keys,
)
from envault.cli_rating import rating_group


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    p = tmp_path / "test.vault"
    p.write_text(json.dumps({}))
    return str(p)


# --- unit tests ---

def test_sidecar_uses_ratings_suffix(vault_path: str) -> None:
    set_rating(vault_path, "API_KEY", 3)
    sidecar = Path(vault_path).with_suffix(".ratings.json")
    assert sidecar.exists()


def test_sidecar_not_created_until_first_set(vault_path: str) -> None:
    sidecar = Path(vault_path).with_suffix(".ratings.json")
    assert not sidecar.exists()


def test_set_rating_persists(vault_path: str) -> None:
    set_rating(vault_path, "DB_PASS", 5)
    assert load_ratings(vault_path)["DB_PASS"] == 5


def test_set_rating_raises_below_min(vault_path: str) -> None:
    with pytest.raises(ValueError, match="between"):
        set_rating(vault_path, "KEY", 0)


def test_set_rating_raises_above_max(vault_path: str) -> None:
    with pytest.raises(ValueError, match="between"):
        set_rating(vault_path, "KEY", 6)


def test_set_rating_empty_key_raises(vault_path: str) -> None:
    with pytest.raises(ValueError, match="empty"):
        set_rating(vault_path, "", 3)


def test_get_rating_returns_none_when_not_set(vault_path: str) -> None:
    assert get_rating(vault_path, "MISSING") is None


def test_remove_rating_returns_true_when_removed(vault_path: str) -> None:
    set_rating(vault_path, "X", 2)
    assert remove_rating(vault_path, "X") is True
    assert get_rating(vault_path, "X") is None


def test_remove_rating_returns_false_when_absent(vault_path: str) -> None:
    assert remove_rating(vault_path, "GHOST") is False


def test_keys_by_rating_returns_sorted(vault_path: str) -> None:
    set_rating(vault_path, "Z_KEY", 4)
    set_rating(vault_path, "A_KEY", 4)
    set_rating(vault_path, "M_KEY", 2)
    assert keys_by_rating(vault_path, 4) == ["A_KEY", "Z_KEY"]


def test_top_keys_returns_highest_first(vault_path: str) -> None:
    set_rating(vault_path, "LOW", 1)
    set_rating(vault_path, "HIGH", 5)
    set_rating(vault_path, "MID", 3)
    result = top_keys(vault_path, 2)
    assert result == ["HIGH", "MID"]


# --- CLI tests ---

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_set_and_show(runner: CliRunner, vault_path: str) -> None:
    result = runner.invoke(rating_group, ["set", "API_KEY", "4", "--vault", vault_path])
    assert result.exit_code == 0
    assert "4" in result.output
    result2 = runner.invoke(rating_group, ["show", "API_KEY", "--vault", vault_path])
    assert "4" in result2.output


def test_cli_list_empty(runner: CliRunner, vault_path: str) -> None:
    result = runner.invoke(rating_group, ["list", "--vault", vault_path])
    assert result.exit_code == 0
    assert "No ratings" in result.output


def test_cli_top(runner: CliRunner, vault_path: str) -> None:
    for key, val in [("A", 5), ("B", 3), ("C", 1)]:
        set_rating(vault_path, key, val)
    result = runner.invoke(rating_group, ["top", "-n", "2", "--vault", vault_path])
    assert result.exit_code == 0
    assert "A" in result.output
    assert "C" not in result.output


def test_cli_set_invalid_rating(runner: CliRunner, vault_path: str) -> None:
    result = runner.invoke(rating_group, ["set", "KEY", "9", "--vault", vault_path])
    assert result.exit_code != 0
