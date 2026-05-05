"""Tests for envault.diff and envault.snapshot."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.diff import VaultDiff, diff_vaults, snapshot_keys
from envault.snapshot import (
    load_snapshot,
    save_snapshot,
    snapshot_diff_summary,
    snapshot_path,
)


# ---------------------------------------------------------------------------
# diff_vaults
# ---------------------------------------------------------------------------

def test_diff_vaults_detects_added():
    old = {"A": "enc1"}
    new = {"A": "enc1", "B": "enc2"}
    d = diff_vaults(old, new)
    assert d.added == ["B"]
    assert d.removed == []
    assert d.changed == []


def test_diff_vaults_detects_removed():
    old = {"A": "enc1", "B": "enc2"}
    new = {"A": "enc1"}
    d = diff_vaults(old, new)
    assert d.removed == ["B"]
    assert d.added == []


def test_diff_vaults_detects_changed():
    old = {"A": "enc_old"}
    new = {"A": "enc_new"}
    d = diff_vaults(old, new)
    assert d.changed == ["A"]


def test_diff_vaults_no_changes():
    vault = {"X": "enc"}
    d = diff_vaults(vault, vault)
    assert not d.has_changes


def test_diff_vaults_empty_vaults():
    """Diffing two empty vaults should report no changes."""
    d = diff_vaults({}, {})
    assert not d.has_changes
    assert d.added == []
    assert d.removed == []
    assert d.changed == []


def test_snapshot_keys_is_sorted_json():
    vault = {"Z": "v", "A": "v", "M": "v"}
    result = snapshot_keys(vault)
    parsed = json.loads(result)
    assert parsed == ["A", "M", "Z"]


# ---------------------------------------------------------------------------
# VaultDiff.summary
# ---------------------------------------------------------------------------

def test_vault_diff_summary_format():
    d = VaultDiff(added=["NEW"], removed=["OLD"], changed=["MOD"])
    summary = d.summary()
    assert "+ NEW" in summary
    assert "- OLD" in summary
    assert "~ MOD" in summary


def test_vault_diff_summary_no_changes():
    d = VaultDiff()
    assert "no changes" in d.summary()


# ---------------------------------------------------------------------------
# snapshot save / load
# ---------------------------------------------------------------------------

def test_save_and_load_snapshot(tmp_path):
    vault = {"DB_URL": "enc1", "API_KEY": "enc2"}
    snap = tmp_path / ".envault.snapshot"
    save_snapshot(vault, snap)
    loaded = load_snapshot(snap)
    assert loaded == ["API_KEY", "DB_URL"]


def test_load_snapshot_missing_file_returns_empty(tmp_path):
    snap = tmp_path / "missing.snapshot"
    assert load_snapshot(snap) == []


def test_snapshot_path_adjacent_to_vault(tmp_path):
    vault_file = tmp_path / "myproject" / ".envault"
    sp = snapshot_path(vault_file)
    assert sp.parent == vault_file.parent
    assert sp.name == ".envault.snapshot"


def test_snapshot_diff_summary_shows_added(tmp_path):
    old_keys = ["EXISTING"]
    new_vault = {"EXISTING": "enc", "FRESH": "enc2"}
    summary = snapshot_diff_summary(old_keys, new_vault)
    assert "+ FRESH" in summary
    assert "- " not in summary


def test_snapshot_diff_summary_shows_removed(tmp_path):
    """Keys present in the old snapshot but absent from the new vault should be marked removed."""
    old_keys = ["GONE", "STILL_HERE"]
    new_vault = {"STILL_HERE": "enc"}
    summary = snapshot_diff_summary(old_keys, new_vault)
    assert "- GONE" in summary
    assert "+ " not in summary
