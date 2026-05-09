"""Tests for envault.checksum."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.checksum import (
    _checksum_path,
    load_checksums,
    record_checksum,
    remove_checksum,
    verify_all,
    verify_checksum,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.vault")


def test_sidecar_uses_checksums_suffix(vault_path: str) -> None:
    assert str(_checksum_path(vault_path)).endswith(".checksums.json")


def test_sidecar_not_created_until_first_record(vault_path: str) -> None:
    assert not _checksum_path(vault_path).exists()


def test_load_checksums_returns_empty_when_no_file(vault_path: str) -> None:
    assert load_checksums(vault_path) == {}


def test_record_checksum_creates_sidecar(vault_path: str) -> None:
    record_checksum(vault_path, "API_KEY", "enc_abc123")
    assert _checksum_path(vault_path).exists()


def test_record_checksum_returns_hex_digest(vault_path: str) -> None:
    digest = record_checksum(vault_path, "API_KEY", "enc_abc123")
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_record_checksum_persists(vault_path: str) -> None:
    record_checksum(vault_path, "DB_URL", "enc_xyz")
    loaded = load_checksums(vault_path)
    assert "DB_URL" in loaded


def test_verify_checksum_true_for_matching_ciphertext(vault_path: str) -> None:
    record_checksum(vault_path, "TOKEN", "enc_val")
    assert verify_checksum(vault_path, "TOKEN", "enc_val") is True


def test_verify_checksum_false_for_tampered_ciphertext(vault_path: str) -> None:
    record_checksum(vault_path, "TOKEN", "enc_val")
    assert verify_checksum(vault_path, "TOKEN", "enc_tampered") is False


def test_verify_checksum_false_when_key_absent(vault_path: str) -> None:
    assert verify_checksum(vault_path, "MISSING_KEY", "anything") is False


def test_remove_checksum_returns_true_when_removed(vault_path: str) -> None:
    record_checksum(vault_path, "KEY", "enc")
    assert remove_checksum(vault_path, "KEY") is True


def test_remove_checksum_returns_false_when_absent(vault_path: str) -> None:
    assert remove_checksum(vault_path, "GHOST") is False


def test_remove_checksum_deletes_entry(vault_path: str) -> None:
    record_checksum(vault_path, "KEY", "enc")
    remove_checksum(vault_path, "KEY")
    assert "KEY" not in load_checksums(vault_path)


def test_verify_all_all_intact(vault_path: str) -> None:
    vault_data = {"A": "enc_a", "B": "enc_b"}
    for k, v in vault_data.items():
        record_checksum(vault_path, k, v)
    results = verify_all(vault_path, vault_data)
    assert results == {"A": True, "B": True}


def test_verify_all_detects_tampered_key(vault_path: str) -> None:
    record_checksum(vault_path, "A", "enc_a")
    record_checksum(vault_path, "B", "enc_b")
    results = verify_all(vault_path, {"A": "enc_a", "B": "enc_tampered"})
    assert results["A"] is True
    assert results["B"] is False


def test_verify_all_missing_checksum_marked_false(vault_path: str) -> None:
    results = verify_all(vault_path, {"UNTRACKED": "enc_x"})
    assert results["UNTRACKED"] is False


def test_sidecar_is_valid_json(vault_path: str) -> None:
    record_checksum(vault_path, "X", "enc_x")
    raw = _checksum_path(vault_path).read_text(encoding="utf-8")
    parsed = json.loads(raw)
    assert isinstance(parsed, dict)
