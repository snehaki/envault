"""Tests for envault.profile and envault.cli_profile."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.profile import (
    create_profile,
    delete_profile,
    get_profile_keys,
    list_profiles,
    load_profiles,
    profile_keys_from_vault,
    PROFILES_FILENAME,
)
from envault.cli_profile import profile_group


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    vp = tmp_path / "vault.json"
    vp.write_text(json.dumps({"secrets": {}}))
    return str(vp)


# --- unit tests for profile module ---

def test_load_profiles_returns_empty_when_no_file(vault_path: str) -> None:
    assert load_profiles(vault_path) == {}


def test_create_profile_persists(vault_path: str) -> None:
    create_profile(vault_path, "dev", ["DB_URL", "SECRET_KEY"])
    profiles = load_profiles(vault_path)
    assert "dev" in profiles
    assert set(profiles["dev"]) == {"DB_URL", "SECRET_KEY"}


def test_create_profile_deduplicates_keys(vault_path: str) -> None:
    create_profile(vault_path, "dev", ["DB_URL", "DB_URL", "SECRET_KEY"])
    assert load_profiles(vault_path)["dev"].count("DB_URL") == 1


def test_create_profile_empty_name_raises(vault_path: str) -> None:
    with pytest.raises(ValueError):
        create_profile(vault_path, "", ["KEY"])


def test_list_profiles_sorted(vault_path: str) -> None:
    create_profile(vault_path, "prod", ["A"])
    create_profile(vault_path, "dev", ["B"])
    assert list_profiles(vault_path) == ["dev", "prod"]


def test_delete_profile_removes_entry(vault_path: str) -> None:
    create_profile(vault_path, "dev", ["A"])
    delete_profile(vault_path, "dev")
    assert "dev" not in load_profiles(vault_path)


def test_delete_profile_missing_raises(vault_path: str) -> None:
    with pytest.raises(KeyError):
        delete_profile(vault_path, "nonexistent")


def test_get_profile_keys_raises_for_missing(vault_path: str) -> None:
    with pytest.raises(KeyError):
        get_profile_keys(vault_path, "ghost")


def test_profile_keys_from_vault_returns_values(vault_path: str) -> None:
    create_profile(vault_path, "dev", ["A", "B"])
    vault_data = {"secrets": {"A": "enc_a", "C": "enc_c"}}
    result = profile_keys_from_vault(vault_path, "dev", vault_data)
    assert result["A"] == "enc_a"
    assert result["B"] is None


# --- CLI integration tests ---

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_profile_save_and_list(runner: CliRunner, vault_path: str) -> None:
    result = runner.invoke(profile_group, ["save", "staging", "DB", "API_KEY", "--vault", vault_path])
    assert result.exit_code == 0
    assert "staging" in result.output

    result = runner.invoke(profile_group, ["list", "--vault", vault_path])
    assert result.exit_code == 0
    assert "staging" in result.output
    assert "DB" in result.output


def test_cli_profile_delete(runner: CliRunner, vault_path: str) -> None:
    runner.invoke(profile_group, ["save", "tmp", "X", "--vault", vault_path])
    result = runner.invoke(profile_group, ["delete", "tmp", "--vault", vault_path])
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_cli_profile_delete_missing_fails(runner: CliRunner, vault_path: str) -> None:
    result = runner.invoke(profile_group, ["delete", "ghost", "--vault", vault_path])
    assert result.exit_code != 0


def test_cli_profile_list_empty(runner: CliRunner, vault_path: str) -> None:
    result = runner.invoke(profile_group, ["list", "--vault", vault_path])
    assert result.exit_code == 0
    assert "No profiles" in result.output
