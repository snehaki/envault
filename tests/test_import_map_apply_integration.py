"""Integration tests: apply_map used together with export.import_env.

Verifies that an import-map translates keys correctly before they are
stored in the vault, simulating the real import workflow.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from envault.crypto import decrypt
from envault.import_map import apply_map, load_map, set_entry
from envault.vault import load_vault, save_vault


PASSPHRASE = "integration-pass"


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    p = tmp_path / "project.vault"
    save_vault(p, {})
    return p


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _import_with_map(
    vault_path: Path,
    raw_env: dict[str, str],
    passphrase: str,
) -> None:
    """Apply the import-map then encrypt each value into the vault."""
    from envault.crypto import encrypt

    mapping = load_map(vault_path)
    translated = apply_map(mapping, raw_env)
    vault = load_vault(vault_path)
    for k, v in translated.items():
        vault[k] = encrypt(v, passphrase)
    save_vault(vault_path, vault)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_apply_map_before_import_renames_keys(vault_path: Path) -> None:
    set_entry(vault_path, "EXT_HOST", "APP_HOST")
    _import_with_map(vault_path, {"EXT_HOST": "db.example.com"}, PASSPHRASE)
    vault = load_vault(vault_path)
    assert "APP_HOST" in vault
    assert "EXT_HOST" not in vault


def test_imported_value_decryptable(vault_path: Path) -> None:
    set_entry(vault_path, "EXT_PORT", "APP_PORT")
    _import_with_map(vault_path, {"EXT_PORT": "5432"}, PASSPHRASE)
    vault = load_vault(vault_path)
    assert decrypt(vault["APP_PORT"], PASSPHRASE) == "5432"


def test_unmapped_keys_pass_through(vault_path: Path) -> None:
    set_entry(vault_path, "ONLY_THIS", "RENAMED")
    raw = {"ONLY_THIS": "val1", "UNTOUCHED": "val2"}
    _import_with_map(vault_path, raw, PASSPHRASE)
    vault = load_vault(vault_path)
    assert "RENAMED" in vault
    assert "UNTOUCHED" in vault


def test_no_map_leaves_keys_unchanged(vault_path: Path) -> None:
    raw = {"FOO": "bar", "BAZ": "qux"}
    _import_with_map(vault_path, raw, PASSPHRASE)
    vault = load_vault(vault_path)
    assert "FOO" in vault
    assert "BAZ" in vault
