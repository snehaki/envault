"""Tests for envault.namespace and cli_namespace."""
from __future__ import annotations

import json
import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.namespace import (
    load_namespaces,
    save_namespaces,
    set_namespace,
    remove_namespace,
    keys_in_namespace,
    list_namespaces,
    _namespaces_path,
)
from envault.cli_namespace import namespace_group


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    p = tmp_path / "test.vault"
    p.write_text("{}")
    return str(p)


# ── unit tests ────────────────────────────────────────────────────────────────

def test_load_namespaces_returns_empty_when_no_file(vault_path):
    assert load_namespaces(vault_path) == {}


def test_sidecar_not_created_until_first_set(vault_path):
    assert not _namespaces_path(vault_path).exists()


def test_set_namespace_persists(vault_path):
    set_namespace(vault_path, "DB_HOST", "database")
    mapping = load_namespaces(vault_path)
    assert mapping["DB_HOST"] == "database"


def test_set_namespace_empty_key_raises(vault_path):
    with pytest.raises(ValueError, match="key"):
        set_namespace(vault_path, "", "database")


def test_set_namespace_empty_namespace_raises(vault_path):
    with pytest.raises(ValueError, match="namespace"):
        set_namespace(vault_path, "DB_HOST", "")


def test_set_namespace_overwrites(vault_path):
    set_namespace(vault_path, "DB_HOST", "database")
    set_namespace(vault_path, "DB_HOST", "infra")
    assert load_namespaces(vault_path)["DB_HOST"] == "infra"


def test_remove_namespace_returns_true_when_removed(vault_path):
    set_namespace(vault_path, "API_KEY", "auth")
    assert remove_namespace(vault_path, "API_KEY") is True
    assert "API_KEY" not in load_namespaces(vault_path)


def test_remove_namespace_returns_false_when_missing(vault_path):
    assert remove_namespace(vault_path, "GHOST") is False


def test_keys_in_namespace_returns_sorted(vault_path):
    set_namespace(vault_path, "DB_PORT", "database")
    set_namespace(vault_path, "DB_HOST", "database")
    set_namespace(vault_path, "API_KEY", "auth")
    assert keys_in_namespace(vault_path, "database") == ["DB_HOST", "DB_PORT"]


def test_list_namespaces_returns_unique_sorted(vault_path):
    set_namespace(vault_path, "DB_HOST", "database")
    set_namespace(vault_path, "API_KEY", "auth")
    set_namespace(vault_path, "DB_PORT", "database")
    assert list_namespaces(vault_path) == ["auth", "database"]


def test_sidecar_is_valid_json(vault_path):
    set_namespace(vault_path, "X", "ns")
    raw = _namespaces_path(vault_path).read_text()
    data = json.loads(raw)
    assert isinstance(data, dict)


# ── CLI tests ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_set_assigns_namespace(runner, vault_path):
    result = runner.invoke(namespace_group, ["set", "DB_HOST", "database", "--vault", vault_path])
    assert result.exit_code == 0
    assert "database" in result.output
    assert load_namespaces(vault_path)["DB_HOST"] == "database"


def test_cli_list_shows_all(runner, vault_path):
    set_namespace(vault_path, "DB_HOST", "database")
    set_namespace(vault_path, "API_KEY", "auth")
    result = runner.invoke(namespace_group, ["list", "--vault", vault_path])
    assert result.exit_code == 0
    assert "DB_HOST" in result.output
    assert "API_KEY" in result.output


def test_cli_list_filtered_by_namespace(runner, vault_path):
    set_namespace(vault_path, "DB_HOST", "database")
    set_namespace(vault_path, "API_KEY", "auth")
    result = runner.invoke(namespace_group, ["list", "--namespace", "database", "--vault", vault_path])
    assert result.exit_code == 0
    assert "DB_HOST" in result.output
    assert "API_KEY" not in result.output


def test_cli_remove_existing(runner, vault_path):
    set_namespace(vault_path, "DB_HOST", "database")
    result = runner.invoke(namespace_group, ["remove", "DB_HOST", "--vault", vault_path])
    assert result.exit_code == 0
    assert load_namespaces(vault_path) == {}


def test_cli_remove_missing_exits_nonzero(runner, vault_path):
    result = runner.invoke(namespace_group, ["remove", "GHOST", "--vault", vault_path])
    assert result.exit_code != 0
