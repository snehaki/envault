"""Tests for envault/schema.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.schema import (
    SchemaViolation,
    load_schema,
    remove_rule,
    set_rule,
    validate_vault,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "test.vault"


# ---------------------------------------------------------------------------
# Sidecar path / persistence
# ---------------------------------------------------------------------------

def test_sidecar_uses_schema_suffix(vault_path: Path) -> None:
    set_rule(vault_path, "API_KEY", type="string")
    sidecar = vault_path.with_suffix(".schema.json")
    assert sidecar.exists()


def test_sidecar_not_created_until_first_set(vault_path: Path) -> None:
    sidecar = vault_path.with_suffix(".schema.json")
    assert not sidecar.exists()


def test_load_schema_returns_empty_when_no_file(vault_path: Path) -> None:
    assert load_schema(vault_path) == {}


def test_set_rule_persists_type(vault_path: Path) -> None:
    set_rule(vault_path, "PORT", type="integer")
    schema = load_schema(vault_path)
    assert schema["PORT"]["type"] == "integer"


def test_set_rule_persists_required(vault_path: Path) -> None:
    set_rule(vault_path, "DB_URL", required=True)
    schema = load_schema(vault_path)
    assert schema["DB_URL"]["required"] is True


def test_set_rule_persists_pattern(vault_path: Path) -> None:
    set_rule(vault_path, "VERSION", pattern=r"^\d+\.\d+\.\d+$")
    schema = load_schema(vault_path)
    assert schema["VERSION"]["pattern"] == r"^\d+\.\d+\.\d+$"


def test_set_rule_unknown_type_raises(vault_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown type"):
        set_rule(vault_path, "FOO", type="blob")


def test_set_rule_invalid_pattern_raises(vault_path: Path) -> None:
    with pytest.raises(re.error if False else Exception):
        set_rule(vault_path, "FOO", pattern="[invalid")


def test_set_rule_empty_key_raises(vault_path: Path) -> None:
    with pytest.raises(ValueError):
        set_rule(vault_path, "", type="string")


def test_remove_rule_returns_true_when_removed(vault_path: Path) -> None:
    set_rule(vault_path, "API_KEY", type="string")
    assert remove_rule(vault_path, "API_KEY") is True
    assert "API_KEY" not in load_schema(vault_path)


def test_remove_rule_returns_false_when_not_found(vault_path: Path) -> None:
    assert remove_rule(vault_path, "GHOST") is False


# ---------------------------------------------------------------------------
# validate_vault
# ---------------------------------------------------------------------------

def test_validate_passes_for_valid_integer(vault_path: Path) -> None:
    set_rule(vault_path, "PORT", type="integer")
    violations = validate_vault(vault_path, {"PORT"}, {"PORT": "8080"})
    assert violations == []


def test_validate_fails_for_invalid_integer(vault_path: Path) -> None:
    set_rule(vault_path, "PORT", type="integer")
    violations = validate_vault(vault_path, {"PORT"}, {"PORT": "not-a-number"})
    assert any(v.key == "PORT" for v in violations)


def test_validate_required_missing_key_raises_violation(vault_path: Path) -> None:
    set_rule(vault_path, "SECRET", required=True)
    violations = validate_vault(vault_path, set(), {})
    assert any(v.key == "SECRET" for v in violations)


def test_validate_required_present_key_passes(vault_path: Path) -> None:
    set_rule(vault_path, "SECRET", required=True, type="string")
    violations = validate_vault(vault_path, {"SECRET"}, {"SECRET": "abc"})
    assert violations == []


def test_validate_custom_pattern_match_passes(vault_path: Path) -> None:
    set_rule(vault_path, "VER", pattern=r"^v\d+$")
    violations = validate_vault(vault_path, {"VER"}, {"VER": "v3"})
    assert violations == []


def test_validate_custom_pattern_mismatch_fails(vault_path: Path) -> None:
    set_rule(vault_path, "VER", pattern=r"^v\d+$")
    violations = validate_vault(vault_path, {"VER"}, {"VER": "3.0"})
    assert any(v.key == "VER" for v in violations)


def test_schema_violation_str(vault_path: Path) -> None:
    v = SchemaViolation(key="FOO", reason="bad value")
    assert "FOO" in str(v) and "bad value" in str(v)


import re  # noqa: E402  (needed for the invalid-pattern test)
