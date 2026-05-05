"""Tests for envault.share — secure vault bundle export/import."""

from __future__ import annotations

import base64
import json
import os
import pytest

from envault.crypto import decrypt
from envault.share import (
    export_bundle,
    import_bundle,
    read_bundle_file,
    write_bundle_file,
)


SRC_PASS = "source-secret"
BUNDLE_PASS = "bundle-secret"
DEST_PASS = "dest-secret"


def _make_vault(passphrase: str) -> dict:
    from envault.crypto import encrypt

    return {
        "DB_URL": encrypt("postgres://localhost/mydb", passphrase),
        "API_KEY": encrypt("abc123", passphrase),
    }


def test_export_bundle_returns_base64_string():
    vault = _make_vault(SRC_PASS)
    bundle = export_bundle(vault, SRC_PASS, BUNDLE_PASS)
    # Must be valid base64
    decoded = base64.b64decode(bundle.encode()).decode()
    data = json.loads(decoded)
    assert set(data.keys()) == {"DB_URL", "API_KEY"}


def test_export_bundle_values_decryptable_with_bundle_pass():
    vault = _make_vault(SRC_PASS)
    bundle = export_bundle(vault, SRC_PASS, BUNDLE_PASS)
    decoded = base64.b64decode(bundle.encode()).decode()
    data = json.loads(decoded)
    assert decrypt(data["DB_URL"], BUNDLE_PASS) == "postgres://localhost/mydb"
    assert decrypt(data["API_KEY"], BUNDLE_PASS) == "abc123"


def test_import_bundle_roundtrip():
    vault = _make_vault(SRC_PASS)
    bundle = export_bundle(vault, SRC_PASS, BUNDLE_PASS)
    imported = import_bundle(bundle, BUNDLE_PASS, DEST_PASS)
    assert set(imported.keys()) == {"DB_URL", "API_KEY"}
    assert decrypt(imported["DB_URL"], DEST_PASS) == "postgres://localhost/mydb"
    assert decrypt(imported["API_KEY"], DEST_PASS) == "abc123"


def test_import_bundle_wrong_passphrase_raises():
    vault = _make_vault(SRC_PASS)
    bundle = export_bundle(vault, SRC_PASS, BUNDLE_PASS)
    with pytest.raises(Exception):
        import_bundle(bundle, "wrong-pass", DEST_PASS)


def test_write_and_read_bundle_file(tmp_path):
    vault = _make_vault(SRC_PASS)
    bundle = export_bundle(vault, SRC_PASS, BUNDLE_PASS)
    path = str(tmp_path / "vault.bundle")
    write_bundle_file(bundle, path)
    assert os.path.exists(path)
    recovered = read_bundle_file(path)
    assert recovered == bundle


def test_bundle_file_contains_newline(tmp_path):
    vault = _make_vault(SRC_PASS)
    bundle = export_bundle(vault, SRC_PASS, BUNDLE_PASS)
    path = str(tmp_path / "vault.bundle")
    write_bundle_file(bundle, path)
    with open(path) as fh:
        raw = fh.read()
    assert raw.endswith("\n")
