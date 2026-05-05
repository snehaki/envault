"""Tests for envault.export (export_env / import_env)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.crypto import decrypt
from envault.export import export_env, import_env
from envault.vault import load_vault, save_vault

PASS = "test-passphrase"


def _make_vault(tmp_path: Path, data: dict[str, str]) -> Path:
    """Helper: create a vault pre-populated with plaintext values."""
    from envault.crypto import encrypt

    vault_path = tmp_path / ".envault"
    vault = {k: encrypt(v, PASS) for k, v in data.items()}
    save_vault(vault_path, vault)
    return vault_path


def test_export_env_returns_correct_lines(tmp_path: Path) -> None:
    vault_path = _make_vault(tmp_path, {"FOO": "bar", "BAZ": "qux"})
    content = export_env(vault_path, PASS)
    assert "FOO=bar" in content
    assert "BAZ=qux" in content


def test_export_env_writes_file(tmp_path: Path) -> None:
    vault_path = _make_vault(tmp_path, {"KEY": "value"})
    out = tmp_path / ".env"
    export_env(vault_path, PASS, out)
    assert out.exists()
    assert "KEY=value" in out.read_text()


def test_export_env_quotes_values_with_spaces(tmp_path: Path) -> None:
    vault_path = _make_vault(tmp_path, {"MSG": "hello world"})
    content = export_env(vault_path, PASS)
    assert 'MSG="hello world"' in content


def test_import_env_stores_encrypted_values(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("ALPHA=one\nBETA=two\n")
    vault_path = tmp_path / ".envault"

    imported = import_env(vault_path, PASS, env_file)
    assert set(imported) == {"ALPHA", "BETA"}

    vault = load_vault(vault_path)
    assert decrypt(vault["ALPHA"], PASS) == "one"
    assert decrypt(vault["BETA"], PASS) == "two"


def test_import_env_skips_comments_and_blanks(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("# comment\n\nVALID=yes\n")
    vault_path = tmp_path / ".envault"

    imported = import_env(vault_path, PASS, env_file)
    assert imported == ["VALID"]


def test_import_env_raises_on_duplicate_without_overwrite(tmp_path: Path) -> None:
    vault_path = _make_vault(tmp_path, {"DUP": "original"})
    env_file = tmp_path / ".env"
    env_file.write_text("DUP=new\n")

    with pytest.raises(ValueError, match="DUP"):
        import_env(vault_path, PASS, env_file, overwrite=False)


def test_import_env_overwrites_when_flag_set(tmp_path: Path) -> None:
    vault_path = _make_vault(tmp_path, {"DUP": "original"})
    env_file = tmp_path / ".env"
    env_file.write_text("DUP=updated\n")

    import_env(vault_path, PASS, env_file, overwrite=True)
    vault = load_vault(vault_path)
    assert decrypt(vault["DUP"], PASS) == "updated"
