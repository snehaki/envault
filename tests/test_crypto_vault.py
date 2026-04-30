"""Tests for envault crypto and vault modules."""

import json
import pytest
from pathlib import Path
from cryptography.exceptions import InvalidTag

from envault.crypto import encrypt, decrypt
from envault.vault import load_vault, save_vault


PASSPHRASE = "hunter2-super-secret"
SAMPLE_DATA = {"DATABASE_URL": "postgres://localhost/db", "SECRET_KEY": "abc123"}


# --- crypto tests ---

def test_encrypt_returns_string():
    result = encrypt("hello", PASSPHRASE)
    assert isinstance(result, str)
    assert len(result) > 0


def test_encrypt_decrypt_roundtrip():
    plaintext = "DATABASE_URL=postgres://localhost/mydb"
    encoded = encrypt(plaintext, PASSPHRASE)
    decoded = decrypt(encoded, PASSPHRASE)
    assert decoded == plaintext


def test_encrypt_produces_different_ciphertexts():
    """Each encryption should produce a unique ciphertext (random nonce/salt)."""
    c1 = encrypt("same", PASSPHRASE)
    c2 = encrypt("same", PASSPHRASE)
    assert c1 != c2


def test_decrypt_wrong_passphrase_raises():
    encoded = encrypt("secret", PASSPHRASE)
    with pytest.raises(InvalidTag):
        decrypt(encoded, "wrong-passphrase")


# --- vault tests ---

def test_save_and_load_vault(tmp_path):
    vault_path = tmp_path / ".env.vault"
    save_vault(vault_path, PASSPHRASE, SAMPLE_DATA)
    assert vault_path.exists()
    loaded = load_vault(vault_path, PASSPHRASE)
    assert loaded == SAMPLE_DATA


def test_load_vault_missing_file_returns_empty(tmp_path):
    vault_path = tmp_path / ".env.vault"
    result = load_vault(vault_path, PASSPHRASE)
    assert result == {}


def test_load_vault_empty_file_returns_empty(tmp_path):
    vault_path = tmp_path / ".env.vault"
    vault_path.write_text("", encoding="utf-8")
    result = load_vault(vault_path, PASSPHRASE)
    assert result == {}


def test_vault_overwrites_key(tmp_path):
    vault_path = tmp_path / ".env.vault"
    save_vault(vault_path, PASSPHRASE, {"KEY": "old"})
    data = load_vault(vault_path, PASSPHRASE)
    data["KEY"] = "new"
    save_vault(vault_path, PASSPHRASE, data)
    reloaded = load_vault(vault_path, PASSPHRASE)
    assert reloaded["KEY"] == "new"
