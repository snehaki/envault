"""Tests for envault.cascade — value propagation to dependent keys."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.crypto import encrypt, decrypt
from envault.vault import save_vault, load_vault
from envault.cascade import cascade_value, CascadeResult


PASS = "hunter2"


def _make_vault(tmp_path: Path, keys: dict[str, str]) -> Path:
    vp = tmp_path / "test.vault"
    data = {k: encrypt(v, PASS) for k, v in keys.items()}
    save_vault(vp, data)
    return vp


def _write_deps(vault_path: Path, deps: dict) -> None:
    sidecar = vault_path.with_suffix(".dependencies.json")
    sidecar.write_text(json.dumps(deps))


# ---------------------------------------------------------------------------
# cascade_value — basic propagation
# ---------------------------------------------------------------------------

def test_cascade_updates_dependent_keys(tmp_path):
    vp = _make_vault(tmp_path, {"DB_PASS": "secret", "APP_DB_PASS": "old"})
    _write_deps(vp, {"DB_PASS": {"dependents": ["APP_DB_PASS"]}})

    result = cascade_value(vp, "DB_PASS", PASS)

    assert "APP_DB_PASS" in result.updated
    vault = load_vault(vp)
    assert decrypt(vault["APP_DB_PASS"], PASS) == "secret"


def test_cascade_returns_correct_result_shape(tmp_path):
    vp = _make_vault(tmp_path, {"SRC": "val", "DST": "old"})
    _write_deps(vp, {"SRC": {"dependents": ["DST"]}})

    result = cascade_value(vp, "SRC", PASS)

    assert isinstance(result, CascadeResult)
    assert result.source_key == "SRC"
    assert result.ok is True


def test_cascade_no_dependents_returns_empty_updated(tmp_path):
    vp = _make_vault(tmp_path, {"SOLO": "alone"})
    _write_deps(vp, {})

    result = cascade_value(vp, "SOLO", PASS)

    assert result.updated == []
    assert result.skipped == []
    assert "no dependents" in result.summary()


def test_cascade_missing_dependent_key_is_skipped(tmp_path):
    vp = _make_vault(tmp_path, {"SRC": "val"})
    _write_deps(vp, {"SRC": {"dependents": ["GHOST"]}})

    result = cascade_value(vp, "SRC", PASS)

    assert "GHOST" in result.skipped
    assert result.ok is False
    assert "skipped" in result.summary()


def test_cascade_source_key_not_found_raises(tmp_path):
    vp = _make_vault(tmp_path, {"OTHER": "x"})
    _write_deps(vp, {})

    with pytest.raises(KeyError, match="MISSING"):
        cascade_value(vp, "MISSING", PASS)


def test_cascade_multiple_dependents(tmp_path):
    vp = _make_vault(tmp_path, {"ROOT": "v", "A": "a", "B": "b"})
    _write_deps(vp, {"ROOT": {"dependents": ["A", "B"]}})

    result = cascade_value(vp, "ROOT", PASS)

    assert set(result.updated) == {"A", "B"}
    vault = load_vault(vp)
    assert decrypt(vault["A"], PASS) == "v"
    assert decrypt(vault["B"], PASS) == "v"
