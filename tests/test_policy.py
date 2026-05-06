"""Tests for envault.policy module."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.policy import (
    _policies_path,
    add_tag,
    get_policy,
    load_policies,
    remove_policy,
    save_policies,
    set_policy,
    validate_value,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.vault")


def test_load_policies_returns_empty_when_no_file(vault_path: str) -> None:
    assert load_policies(vault_path) == {}


def test_set_policy_persists(vault_path: str) -> None:
    set_policy(vault_path, "DB_PASSWORD", "min_length", 12)
    policies = load_policies(vault_path)
    assert policies["DB_PASSWORD"]["min_length"] == 12


def test_set_policy_multiple_rules(vault_path: str) -> None:
    set_policy(vault_path, "API_KEY", "min_length", 8)
    set_policy(vault_path, "API_KEY", "no_spaces", True)
    rules = get_policy(vault_path, "API_KEY")
    assert rules["min_length"] == 8
    assert rules["no_spaces"] is True


def test_set_policy_unknown_rule_raises(vault_path: str) -> None:
    with pytest.raises(ValueError, match="Unknown policy rule"):
        set_policy(vault_path, "KEY", "banana", 5)


def test_get_policy_returns_empty_for_unknown_key(vault_path: str) -> None:
    assert get_policy(vault_path, "MISSING") == {}


def test_remove_policy_returns_true_when_removed(vault_path: str) -> None:
    set_policy(vault_path, "FOO", "required", True)
    assert remove_policy(vault_path, "FOO") is True
    assert get_policy(vault_path, "FOO") == {}


def test_remove_policy_returns_false_when_not_found(vault_path: str) -> None:
    assert remove_policy(vault_path, "NONEXISTENT") is False


def test_validate_value_passes_when_no_violations() -> None:
    issues = validate_value("KEY", "secret123", {"min_length": 5, "no_spaces": True})
    assert issues == []


def test_validate_value_min_length_violation() -> None:
    issues = validate_value("KEY", "abc", {"min_length": 8})
    assert any("min_length" in i for i in issues)


def test_validate_value_max_length_violation() -> None:
    issues = validate_value("KEY", "a" * 20, {"max_length": 10})
    assert any("max_length" in i for i in issues)


def test_validate_value_no_spaces_violation() -> None:
    issues = validate_value("KEY", "has spaces", {"no_spaces": True})
    assert any("spaces" in i for i in issues)


def test_validate_value_pattern_violation() -> None:
    issues = validate_value("KEY", "abc", {"pattern": r"[0-9]+"})
    assert any("pattern" in i for i in issues)


def test_validate_value_required_empty() -> None:
    issues = validate_value("KEY", "", {"required": True})
    assert any("required" in i for i in issues)


def test_policies_sidecar_path(vault_path: str) -> None:
    p = _policies_path(vault_path)
    assert str(p).endswith(".policies.json")
