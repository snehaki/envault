"""Tests verifying the policy sidecar file behaviour."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.policy import _policies_path, load_policies, set_policy


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "myproject.vault")


def test_sidecar_uses_policies_suffix(vault_path: str) -> None:
    p = _policies_path(vault_path)
    assert p.name.endswith(".policies.json")


def test_sidecar_not_created_until_first_set(vault_path: str) -> None:
    p = _policies_path(vault_path)
    assert not p.exists()
    load_policies(vault_path)  # read-only, should not create file
    assert not p.exists()


def test_sidecar_created_after_set(vault_path: str) -> None:
    set_policy(vault_path, "SECRET", "required", True)
    p = _policies_path(vault_path)
    assert p.exists()


def test_sidecar_is_valid_json(vault_path: str) -> None:
    set_policy(vault_path, "TOKEN", "min_length", 16)
    p = _policies_path(vault_path)
    data = json.loads(p.read_text())
    assert isinstance(data, dict)
    assert "TOKEN" in data


def test_sidecar_preserves_multiple_keys(vault_path: str) -> None:
    set_policy(vault_path, "A", "required", True)
    set_policy(vault_path, "B", "min_length", 4)
    set_policy(vault_path, "C", "no_spaces", True)
    policies = load_policies(vault_path)
    assert len(policies) == 3
    assert "A" in policies
    assert "B" in policies
    assert "C" in policies
