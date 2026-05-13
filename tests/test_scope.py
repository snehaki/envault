"""Tests for envault.scope."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.scope import (
    get_scopes,
    keys_in_scope,
    load_scopes,
    remove_scope,
    set_scope,
    valid_scopes,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.vault")


def test_sidecar_uses_scopes_suffix(vault_path: str) -> None:
    set_scope(vault_path, "DB_URL", ["prod"])
    sidecar = Path(vault_path).with_suffix(".scopes.json")
    assert sidecar.exists()


def test_sidecar_not_created_until_first_set(vault_path: str) -> None:
    sidecar = Path(vault_path).with_suffix(".scopes.json")
    assert not sidecar.exists()


def test_load_scopes_returns_empty_when_no_file(vault_path: str) -> None:
    assert load_scopes(vault_path) == {}


def test_set_scope_persists(vault_path: str) -> None:
    set_scope(vault_path, "API_KEY", ["dev", "staging"])
    result = get_scopes(vault_path, "API_KEY")
    assert result == ["dev", "staging"]


def test_set_scope_deduplicates(vault_path: str) -> None:
    set_scope(vault_path, "API_KEY", ["dev", "dev", "prod"])
    assert get_scopes(vault_path, "API_KEY") == ["dev", "prod"]


def test_set_scope_sorts_scopes(vault_path: str) -> None:
    set_scope(vault_path, "X", ["staging", "dev"])
    assert get_scopes(vault_path, "X") == ["dev", "staging"]


def test_set_scope_unknown_raises(vault_path: str) -> None:
    with pytest.raises(ValueError, match="Unknown scopes"):
        set_scope(vault_path, "KEY", ["unknown_env"])


def test_set_scope_empty_key_raises(vault_path: str) -> None:
    with pytest.raises(ValueError, match="key must not be empty"):
        set_scope(vault_path, "", ["dev"])


def test_remove_scope_returns_true_when_removed(vault_path: str) -> None:
    set_scope(vault_path, "DB_URL", ["prod"])
    assert remove_scope(vault_path, "DB_URL") is True


def test_remove_scope_returns_false_when_missing(vault_path: str) -> None:
    assert remove_scope(vault_path, "NONEXISTENT") is False


def test_remove_scope_deletes_entry(vault_path: str) -> None:
    set_scope(vault_path, "DB_URL", ["prod"])
    remove_scope(vault_path, "DB_URL")
    assert get_scopes(vault_path, "DB_URL") == []


def test_get_scopes_returns_empty_for_unscoped_key(vault_path: str) -> None:
    set_scope(vault_path, "OTHER", ["dev"])
    assert get_scopes(vault_path, "UNSCOPED_KEY") == []


def test_keys_in_scope_returns_matching_keys(vault_path: str) -> None:
    set_scope(vault_path, "DB_URL", ["prod", "staging"])
    set_scope(vault_path, "DEBUG", ["dev"])
    set_scope(vault_path, "API_KEY", ["prod"])
    assert keys_in_scope(vault_path, "prod") == ["API_KEY", "DB_URL"]


def test_keys_in_scope_returns_empty_for_unused_scope(vault_path: str) -> None:
    set_scope(vault_path, "DB_URL", ["dev"])
    assert keys_in_scope(vault_path, "prod") == []


def test_valid_scopes_returns_sorted_list() -> None:
    scopes = valid_scopes()
    assert scopes == sorted(scopes)
    assert "dev" in scopes
    assert "prod" in scopes


def test_sidecar_is_valid_json(vault_path: str) -> None:
    set_scope(vault_path, "KEY", ["dev"])
    sidecar = Path(vault_path).with_suffix(".scopes.json")
    data = json.loads(sidecar.read_text())
    assert isinstance(data, dict)
