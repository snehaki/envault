"""Tests for envault.annotation module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.annotation import (
    get_annotation,
    list_annotations,
    load_annotations,
    remove_annotation,
    set_annotation,
)
from envault.cli_annotation import annotation_group


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.vault")


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_sidecar_uses_annotations_suffix(vault_path: str) -> None:
    set_annotation(vault_path, "API_KEY", "The main API key")
    sidecar = Path(vault_path).with_suffix(".annotations.json")
    assert sidecar.exists()


def test_sidecar_not_created_until_first_set(vault_path: str) -> None:
    sidecar = Path(vault_path).with_suffix(".annotations.json")
    assert not sidecar.exists()


def test_load_annotations_returns_empty_when_no_file(vault_path: str) -> None:
    assert load_annotations(vault_path) == {}


def test_set_annotation_persists(vault_path: str) -> None:
    set_annotation(vault_path, "DB_URL", "Primary database connection string")
    assert get_annotation(vault_path, "DB_URL") == "Primary database connection string"


def test_set_annotation_overwrites_existing(vault_path: str) -> None:
    set_annotation(vault_path, "DB_URL", "old note")
    set_annotation(vault_path, "DB_URL", "new note")
    assert get_annotation(vault_path, "DB_URL") == "new note"


def test_get_annotation_returns_none_when_not_set(vault_path: str) -> None:
    assert get_annotation(vault_path, "MISSING") is None


def test_remove_annotation_returns_true_when_removed(vault_path: str) -> None:
    set_annotation(vault_path, "FOO", "bar")
    assert remove_annotation(vault_path, "FOO") is True


def test_remove_annotation_returns_false_when_missing(vault_path: str) -> None:
    assert remove_annotation(vault_path, "NOPE") is False


def test_remove_annotation_deletes_key(vault_path: str) -> None:
    set_annotation(vault_path, "FOO", "bar")
    remove_annotation(vault_path, "FOO")
    assert get_annotation(vault_path, "FOO") is None


def test_list_annotations_sorted(vault_path: str) -> None:
    set_annotation(vault_path, "Z_KEY", "last")
    set_annotation(vault_path, "A_KEY", "first")
    keys = list(list_annotations(vault_path).keys())
    assert keys == ["A_KEY", "Z_KEY"]


def test_set_annotation_empty_key_raises(vault_path: str) -> None:
    with pytest.raises(ValueError):
        set_annotation(vault_path, "", "some text")


def test_sidecar_is_valid_json(vault_path: str) -> None:
    set_annotation(vault_path, "KEY", "note")
    sidecar = Path(vault_path).with_suffix(".annotations.json")
    data = json.loads(sidecar.read_text())
    assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_set_and_show(runner: CliRunner, vault_path: str) -> None:
    result = runner.invoke(annotation_group, ["set", "API_KEY", "my note", "--vault", vault_path])
    assert result.exit_code == 0
    result = runner.invoke(annotation_group, ["show", "API_KEY", "--vault", vault_path])
    assert result.exit_code == 0
    assert "my note" in result.output


def test_cli_list_shows_entries(runner: CliRunner, vault_path: str) -> None:
    runner.invoke(annotation_group, ["set", "A", "note a", "--vault", vault_path])
    runner.invoke(annotation_group, ["set", "B", "note b", "--vault", vault_path])
    result = runner.invoke(annotation_group, ["list", "--vault", vault_path])
    assert "A: note a" in result.output
    assert "B: note b" in result.output


def test_cli_remove_existing(runner: CliRunner, vault_path: str) -> None:
    runner.invoke(annotation_group, ["set", "KEY", "text", "--vault", vault_path])
    result = runner.invoke(annotation_group, ["remove", "KEY", "--vault", vault_path])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_cli_list_empty(runner: CliRunner, vault_path: str) -> None:
    result = runner.invoke(annotation_group, ["list", "--vault", vault_path])
    assert result.exit_code == 0
    assert "No annotations" in result.output
