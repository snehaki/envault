"""Tests for envault.sync module."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from envault.crypto import decrypt, encrypt
from envault.sync import ConflictStrategy, SyncResult, sync_vaults
from envault.vault import save_vault


LOCAL_PASS = "local-secret"
REMOTE_PASS = "remote-secret"


def _make_vault(path: str, passphrase: str, keys: dict[str, str]) -> None:
    secrets = {k: encrypt(v, passphrase) for k, v in keys.items()}
    save_vault(path, {"secrets": secrets})


@pytest.fixture()
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def test_sync_adds_new_keys(tmp_dir):
    local = os.path.join(tmp_dir, "local.vault")
    remote = os.path.join(tmp_dir, "remote.vault")
    _make_vault(local, LOCAL_PASS, {"EXISTING": "old"})
    _make_vault(remote, REMOTE_PASS, {"NEW_KEY": "hello"})

    result = sync_vaults(local, remote, LOCAL_PASS, REMOTE_PASS)

    assert "NEW_KEY" in result.added
    assert result.updated == []
    assert result.skipped == []


def test_sync_added_key_decryptable(tmp_dir):
    local = os.path.join(tmp_dir, "local.vault")
    remote = os.path.join(tmp_dir, "remote.vault")
    _make_vault(local, LOCAL_PASS, {})
    _make_vault(remote, REMOTE_PASS, {"DB_URL": "postgres://localhost/db"})

    sync_vaults(local, remote, LOCAL_PASS, REMOTE_PASS)

    from envault.vault import load_vault
    vault = load_vault(local)
    plaintext = decrypt(vault["secrets"]["DB_URL"], LOCAL_PASS)
    assert plaintext == "postgres://localhost/db"


def test_sync_keep_local_on_conflict(tmp_dir):
    local = os.path.join(tmp_dir, "local.vault")
    remote = os.path.join(tmp_dir, "remote.vault")
    _make_vault(local, LOCAL_PASS, {"SHARED": "local-value"})
    _make_vault(remote, REMOTE_PASS, {"SHARED": "remote-value"})

    result = sync_vaults(local, remote, LOCAL_PASS, REMOTE_PASS,
                         strategy=ConflictStrategy.KEEP_LOCAL)

    assert "SHARED" in result.skipped
    from envault.vault import load_vault
    vault = load_vault(local)
    assert decrypt(vault["secrets"]["SHARED"], LOCAL_PASS) == "local-value"


def test_sync_take_remote_on_conflict(tmp_dir):
    local = os.path.join(tmp_dir, "local.vault")
    remote = os.path.join(tmp_dir, "remote.vault")
    _make_vault(local, LOCAL_PASS, {"SHARED": "local-value"})
    _make_vault(remote, REMOTE_PASS, {"SHARED": "remote-value"})

    result = sync_vaults(local, remote, LOCAL_PASS, REMOTE_PASS,
                         strategy=ConflictStrategy.TAKE_REMOTE)

    assert "SHARED" in result.updated
    from envault.vault import load_vault
    vault = load_vault(local)
    assert decrypt(vault["secrets"]["SHARED"], LOCAL_PASS) == "remote-value"


def test_sync_specific_keys_only(tmp_dir):
    local = os.path.join(tmp_dir, "local.vault")
    remote = os.path.join(tmp_dir, "remote.vault")
    _make_vault(local, LOCAL_PASS, {})
    _make_vault(remote, REMOTE_PASS, {"A": "1", "B": "2", "C": "3"})

    result = sync_vaults(local, remote, LOCAL_PASS, REMOTE_PASS, keys=["A", "C"])

    assert sorted(result.added) == ["A", "C"]
    from envault.vault import load_vault
    vault = load_vault(local)
    assert "B" not in vault["secrets"]


def test_sync_result_summary_no_changes(tmp_dir):
    local = os.path.join(tmp_dir, "local.vault")
    remote = os.path.join(tmp_dir, "remote.vault")
    _make_vault(local, LOCAL_PASS, {"X": "val"})
    _make_vault(remote, REMOTE_PASS, {"X": "other"})

    result = sync_vaults(local, remote, LOCAL_PASS, REMOTE_PASS,
                         strategy=ConflictStrategy.KEEP_LOCAL)
    assert result.summary() == "1 skipped"


def test_sync_result_summary_mixed(tmp_dir):
    local = os.path.join(tmp_dir, "local.vault")
    remote = os.path.join(tmp_dir, "remote.vault")
    _make_vault(local, LOCAL_PASS, {"EXISTING": "e"})
    _make_vault(remote, REMOTE_PASS, {"NEW": "n", "EXISTING": "e2"})

    result = sync_vaults(local, remote, LOCAL_PASS, REMOTE_PASS,
                         strategy=ConflictStrategy.TAKE_REMOTE)
    assert "added" in result.summary()
    assert "updated" in result.summary()
