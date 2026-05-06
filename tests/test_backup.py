"""Tests for envault.backup."""

from __future__ import annotations

import json
import base64
from pathlib import Path

import pytest

from envault.backup import (
    create_backup,
    write_backup_file,
    read_backup_file,
    restore_backup,
    BACKUP_VERSION,
)
from envault.vault import load_vault, save_vault
from envault.crypto import encrypt


PASS = "hunter2"


def _make_vault(tmp_path: Path) -> Path:
    vault_path = tmp_path / "test.vault"
    data = {
        "DB_URL": encrypt("postgres://localhost/db", PASS),
        "SECRET": encrypt("s3cr3t", PASS),
    }
    save_vault(vault_path, data)
    return vault_path


def test_create_backup_contains_version(tmp_path):
    vault_path = _make_vault(tmp_path)
    backup = create_backup(vault_path)
    assert backup["version"] == BACKUP_VERSION


def test_create_backup_embeds_vault_keys(tmp_path):
    vault_path = _make_vault(tmp_path)
    backup = create_backup(vault_path)
    assert "DB_URL" in backup["vault"]
    assert "SECRET" in backup["vault"]


def test_create_backup_has_checksum(tmp_path):
    vault_path = _make_vault(tmp_path)
    backup = create_backup(vault_path)
    assert "checksum" in backup
    assert len(backup["checksum"]) == 16


def test_write_and_read_backup_roundtrip(tmp_path):
    vault_path = _make_vault(tmp_path)
    backup_file = tmp_path / "vault.bak"
    write_backup_file(vault_path, backup_file)

    assert backup_file.exists()
    payload = read_backup_file(backup_file)
    assert payload["vault"].keys() == {"DB_URL", "SECRET"}


def test_read_backup_raises_on_corrupted_file(tmp_path):
    bad_file = tmp_path / "bad.bak"
    bad_file.write_text("not-base64!!")
    with pytest.raises(ValueError, match="Cannot read backup file"):
        read_backup_file(bad_file)


def test_read_backup_raises_on_checksum_mismatch(tmp_path):
    vault_path = _make_vault(tmp_path)
    backup_file = tmp_path / "vault.bak"
    write_backup_file(vault_path, backup_file)

    # Tamper with the payload
    raw = json.loads(base64.b64decode(backup_file.read_text()))
    raw["vault"]["INJECTED"] = "evil"
    backup_file.write_text(base64.b64encode(json.dumps(raw).encode()).decode())

    with pytest.raises(ValueError, match="checksum mismatch"):
        read_backup_file(backup_file)


def test_restore_backup_writes_vault(tmp_path):
    vault_path = _make_vault(tmp_path)
    backup_file = tmp_path / "vault.bak"
    write_backup_file(vault_path, backup_file)

    restored_path = tmp_path / "restored.vault"
    result = restore_backup(backup_file, dest_vault=restored_path)

    assert result == restored_path
    restored = load_vault(restored_path)
    assert set(restored.keys()) == {"DB_URL", "SECRET"}


def test_restore_backup_uses_source_path_when_no_dest(tmp_path):
    vault_path = _make_vault(tmp_path)
    backup_file = tmp_path / "vault.bak"
    write_backup_file(vault_path, backup_file)

    vault_path.unlink()  # remove original
    result = restore_backup(backup_file)

    assert result == vault_path
    assert vault_path.exists()
