"""Tests for envault.alias and envault.cli_alias."""

from __future__ import annotations

import json
import pytest
from click.testing import CliRunner

from envault.alias import (
    load_aliases,
    list_aliases,
    remove_alias,
    resolve_alias,
    set_alias,
    _aliases_path,
)
from envault.cli_alias import alias_group


# ---------------------------------------------------------------------------
# Unit tests for alias.py
# ---------------------------------------------------------------------------


def test_load_aliases_returns_empty_when_no_file(tmp_path):
    vault = str(tmp_path / "vault.json")
    assert load_aliases(vault) == {}


def test_set_alias_persists(tmp_path):
    vault = str(tmp_path / "vault.json")
    set_alias(vault, "db", "DATABASE_URL")
    aliases = load_aliases(vault)
    assert aliases["db"] == "DATABASE_URL"


def test_set_alias_overwrites_existing(tmp_path):
    vault = str(tmp_path / "vault.json")
    set_alias(vault, "db", "DATABASE_URL")
    set_alias(vault, "db", "POSTGRES_URL")
    assert load_aliases(vault)["db"] == "POSTGRES_URL"


def test_set_alias_empty_name_raises(tmp_path):
    vault = str(tmp_path / "vault.json")
    with pytest.raises(ValueError, match="Alias name"):
        set_alias(vault, "", "SOME_KEY")


def test_set_alias_empty_key_raises(tmp_path):
    vault = str(tmp_path / "vault.json")
    with pytest.raises(ValueError, match="Target key"):
        set_alias(vault, "myalias", "")


def test_remove_alias_returns_true_when_removed(tmp_path):
    vault = str(tmp_path / "vault.json")
    set_alias(vault, "db", "DATABASE_URL")
    assert remove_alias(vault, "db") is True
    assert load_aliases(vault) == {}


def test_remove_alias_returns_false_when_not_found(tmp_path):
    vault = str(tmp_path / "vault.json")
    assert remove_alias(vault, "ghost") is False


def test_resolve_alias_returns_key(tmp_path):
    vault = str(tmp_path / "vault.json")
    set_alias(vault, "sec", "SECRET_KEY")
    assert resolve_alias(vault, "sec") == "SECRET_KEY"


def test_resolve_alias_returns_none_for_unknown(tmp_path):
    vault = str(tmp_path / "vault.json")
    assert resolve_alias(vault, "nope") is None


def test_list_aliases_sorted(tmp_path):
    vault = str(tmp_path / "vault.json")
    set_alias(vault, "zzz", "Z_KEY")
    set_alias(vault, "aaa", "A_KEY")
    keys = list(list_aliases(vault).keys())
    assert keys == sorted(keys)


def test_sidecar_uses_aliases_suffix(tmp_path):
    vault = str(tmp_path / "vault.json")
    set_alias(vault, "x", "X_KEY")
    sidecar = _aliases_path(vault)
    assert sidecar.exists()
    assert sidecar.name == "vault.aliases.json"


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path):
    return str(tmp_path / "vault.json")


def test_cli_alias_set_and_list(runner, vault_file):
    result = runner.invoke(alias_group, ["set", "db", "DATABASE_URL", "--vault", vault_file])
    assert result.exit_code == 0
    assert "db" in result.output

    result = runner.invoke(alias_group, ["list", "--vault", vault_file])
    assert result.exit_code == 0
    assert "db" in result.output
    assert "DATABASE_URL" in result.output


def test_cli_alias_resolve(runner, vault_file):
    runner.invoke(alias_group, ["set", "sec", "SECRET_KEY", "--vault", vault_file])
    result = runner.invoke(alias_group, ["resolve", "sec", "--vault", vault_file])
    assert result.exit_code == 0
    assert "SECRET_KEY" in result.output


def test_cli_alias_resolve_unknown_fails(runner, vault_file):
    result = runner.invoke(alias_group, ["resolve", "ghost", "--vault", vault_file])
    assert result.exit_code != 0


def test_cli_alias_remove(runner, vault_file):
    runner.invoke(alias_group, ["set", "tmp", "TMP_KEY", "--vault", vault_file])
    result = runner.invoke(alias_group, ["remove", "tmp", "--vault", vault_file])
    assert result.exit_code == 0
    result = runner.invoke(alias_group, ["list", "--vault", vault_file])
    assert "tmp" not in result.output


def test_cli_alias_remove_unknown_fails(runner, vault_file):
    result = runner.invoke(alias_group, ["remove", "ghost", "--vault", vault_file])
    assert result.exit_code != 0


def test_cli_alias_list_empty(runner, vault_file):
    result = runner.invoke(alias_group, ["list", "--vault", vault_file])
    assert result.exit_code == 0
    assert "No aliases" in result.output
