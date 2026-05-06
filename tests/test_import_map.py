"""Tests for envault.import_map."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.import_map import (
    _map_path,
    apply_map,
    load_map,
    remove_entry,
    save_map,
    set_entry,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "test.vault"


# ---------------------------------------------------------------------------
# Sidecar path
# ---------------------------------------------------------------------------

def test_sidecar_uses_importmap_suffix(vault_path: Path) -> None:
    assert _map_path(vault_path).name == "test.importmap.json"


def test_sidecar_not_created_until_first_set(vault_path: Path) -> None:
    _ = load_map(vault_path)  # read-only
    assert not _map_path(vault_path).exists()


# ---------------------------------------------------------------------------
# load / save round-trip
# ---------------------------------------------------------------------------

def test_load_map_returns_empty_when_no_file(vault_path: Path) -> None:
    assert load_map(vault_path) == {}


def test_save_and_load_map_roundtrip(vault_path: Path) -> None:
    mapping = {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"}
    save_map(vault_path, mapping)
    assert load_map(vault_path) == mapping


def test_sidecar_is_valid_json(vault_path: Path) -> None:
    save_map(vault_path, {"FOO": "BAR"})
    raw = json.loads(_map_path(vault_path).read_text())
    assert raw == {"FOO": "BAR"}


# ---------------------------------------------------------------------------
# set_entry
# ---------------------------------------------------------------------------

def test_set_entry_creates_mapping(vault_path: Path) -> None:
    set_entry(vault_path, "OLD_KEY", "NEW_KEY")
    assert load_map(vault_path)["OLD_KEY"] == "NEW_KEY"


def test_set_entry_overwrites_existing(vault_path: Path) -> None:
    set_entry(vault_path, "OLD_KEY", "FIRST")
    set_entry(vault_path, "OLD_KEY", "SECOND")
    assert load_map(vault_path)["OLD_KEY"] == "SECOND"


def test_set_entry_empty_source_raises(vault_path: Path) -> None:
    with pytest.raises(ValueError, match="source_key"):
        set_entry(vault_path, "", "TARGET")


def test_set_entry_empty_target_raises(vault_path: Path) -> None:
    with pytest.raises(ValueError, match="target_key"):
        set_entry(vault_path, "SOURCE", "")


# ---------------------------------------------------------------------------
# remove_entry
# ---------------------------------------------------------------------------

def test_remove_entry_returns_true_when_removed(vault_path: Path) -> None:
    set_entry(vault_path, "A", "B")
    assert remove_entry(vault_path, "A") is True
    assert "A" not in load_map(vault_path)


def test_remove_entry_returns_false_when_missing(vault_path: Path) -> None:
    assert remove_entry(vault_path, "NONEXISTENT") is False


# ---------------------------------------------------------------------------
# apply_map
# ---------------------------------------------------------------------------

def test_apply_map_renames_keys() -> None:
    mapping = {"DB_HOST": "DATABASE_HOST"}
    env = {"DB_HOST": "localhost", "PORT": "5432"}
    result = apply_map(mapping, env)
    assert result == {"DATABASE_HOST": "localhost", "PORT": "5432"}


def test_apply_map_passthrough_when_empty() -> None:
    env = {"FOO": "bar", "BAZ": "qux"}
    assert apply_map({}, env) == env


def test_apply_map_does_not_mutate_original() -> None:
    env = {"KEY": "value"}
    apply_map({"KEY": "NEW_KEY"}, env)
    assert "KEY" in env
