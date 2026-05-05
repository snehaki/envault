"""Tests for envault.rotate.rotate_key."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.crypto import decrypt, encrypt
from envault.rotate import rotate_key
from envault.vault import load_vault, save_vault


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vault(tmp_path: Path, passphrase: str, data: dict[str, str]) -> Path:
    vault_path = tmp_path / ".envault.json"
    secrets = {k: encrypt(v, passphrase) for k, v in data.items()}
    save_vault(vault_path, {"secrets": secrets})
    return vault_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_rotate_key_returns_rotated_keys(tmp_path):
    vault_path = _make_vault(tmp_path, "old-pass", {"DB_URL": "postgres://", "API_KEY": "abc"})
    rotated = rotate_key(vault_path, "old-pass", "new-pass")
    assert set(rotated) == {"DB_URL", "API_KEY"}


def test_rotate_key_new_passphrase_decrypts_correctly(tmp_path):
    vault_path = _make_vault(tmp_path, "old-pass", {"SECRET": "hunter2"})
    rotate_key(vault_path, "old-pass", "new-pass")

    vault = load_vault(vault_path)
    plaintext = decrypt(vault["secrets"]["SECRET"], "new-pass")
    assert plaintext == "hunter2"


def test_rotate_key_old_passphrase_no_longer_works(tmp_path):
    vault_path = _make_vault(tmp_path, "old-pass", {"TOKEN": "tok_123"})
    rotate_key(vault_path, "old-pass", "new-pass")

    vault = load_vault(vault_path)
    with pytest.raises(Exception):
        decrypt(vault["secrets"]["TOKEN"], "old-pass")


def test_rotate_key_wrong_old_passphrase_raises(tmp_path):
    vault_path = _make_vault(tmp_path, "correct-pass", {"X": "value"})
    with pytest.raises(ValueError, match="old passphrase"):
        rotate_key(vault_path, "wrong-pass", "new-pass")


def test_rotate_key_vault_unchanged_on_failure(tmp_path):
    vault_path = _make_vault(tmp_path, "correct-pass", {"X": "value"})
    original_text = vault_path.read_text()

    with pytest.raises(ValueError):
        rotate_key(vault_path, "wrong-pass", "new-pass")

    assert vault_path.read_text() == original_text


def test_rotate_key_empty_vault_returns_empty_list(tmp_path):
    vault_path = tmp_path / ".envault.json"
    save_vault(vault_path, {"secrets": {}})
    rotated = rotate_key(vault_path, "any-pass", "new-pass")
    assert rotated == []
