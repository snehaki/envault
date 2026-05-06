"""Tests for envault.env_diff.compare_env_to_vault."""
from __future__ import annotations

import json
import os
import pytest

from envault.crypto import encrypt
from envault.env_diff import compare_env_to_vault, EnvDiffResult


PASS = "hunter2"


def _make_vault(tmp_path, keys: dict) -> str:
    """Write a minimal vault file with encrypted secrets."""
    secrets = {k: encrypt(v, PASS) for k, v in keys.items()}
    vault = {"secrets": secrets}
    p = tmp_path / "test.vault"
    p.write_text(json.dumps(vault))
    return str(p)


def test_all_match(tmp_path):
    vp = _make_vault(tmp_path, {"FOO": "bar", "BAZ": "qux"})
    result = compare_env_to_vault(vp, PASS, env={"FOO": "bar", "BAZ": "qux"}, include_extra=False)
    assert result.ok
    assert set(result.matched) == {"FOO", "BAZ"}
    assert result.missing == []
    assert result.mismatched == []


def test_detects_missing_key(tmp_path):
    vp = _make_vault(tmp_path, {"FOO": "bar", "SECRET": "s3cr3t"})
    result = compare_env_to_vault(vp, PASS, env={"FOO": "bar"}, include_extra=False)
    assert not result.ok
    assert "SECRET" in result.missing
    assert "FOO" in result.matched


def test_detects_mismatched_value(tmp_path):
    vp = _make_vault(tmp_path, {"FOO": "correct"})
    result = compare_env_to_vault(vp, PASS, env={"FOO": "wrong"}, include_extra=False)
    assert not result.ok
    assert "FOO" in result.mismatched
    assert result.missing == []


def test_detects_extra_keys(tmp_path):
    vp = _make_vault(tmp_path, {"FOO": "bar"})
    result = compare_env_to_vault(vp, PASS, env={"FOO": "bar", "EXTRA": "x"}, include_extra=True)
    assert "EXTRA" in result.extra


def test_extra_keys_excluded_when_flag_false(tmp_path):
    vp = _make_vault(tmp_path, {"FOO": "bar"})
    result = compare_env_to_vault(vp, PASS, env={"FOO": "bar", "EXTRA": "x"}, include_extra=False)
    assert result.extra == []


def test_wrong_passphrase_marks_mismatch(tmp_path):
    vp = _make_vault(tmp_path, {"FOO": "bar"})
    result = compare_env_to_vault(vp, "wrongpass", env={"FOO": "bar"}, include_extra=False)
    assert "FOO" in result.mismatched


def test_summary_contains_labels(tmp_path):
    vp = _make_vault(tmp_path, {"MATCH": "v", "MISS": "x"})
    result = compare_env_to_vault(vp, PASS, env={"MATCH": "v", "EXTRA_KEY": "e"}, include_extra=True)
    s = result.summary()
    assert "MISSING" in s
    assert "EXTRA" in s
    assert "OK" in s


def test_empty_vault_no_missing(tmp_path):
    vp = _make_vault(tmp_path, {})
    result = compare_env_to_vault(vp, PASS, env={"SOME": "val"}, include_extra=False)
    assert result.ok
    assert result.missing == []
