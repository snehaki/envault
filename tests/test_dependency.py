"""Tests for envault.dependency."""
from __future__ import annotations

import json
import pytest

from envault.dependency import (
    _deps_path,
    get_dependents,
    load_dependencies,
    remove_dependency,
    resolve_order,
    save_dependencies,
    set_dependency,
)


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "test.vault")


def test_sidecar_uses_dependencies_suffix(vault_path):
    p = _deps_path(vault_path)
    assert p.name.endswith(".dependencies.json")


def test_sidecar_not_created_until_first_set(vault_path):
    assert not _deps_path(vault_path).exists()


def test_load_dependencies_returns_empty_when_no_file(vault_path):
    assert load_dependencies(vault_path) == {}


def test_set_dependency_persists(vault_path):
    set_dependency(vault_path, "DB_URL", ["DB_HOST", "DB_PORT"])
    deps = load_dependencies(vault_path)
    assert deps["DB_URL"] == ["DB_HOST", "DB_PORT"]


def test_set_dependency_deduplicates(vault_path):
    set_dependency(vault_path, "A", ["B", "B", "C"])
    deps = load_dependencies(vault_path)
    assert deps["A"] == ["B", "C"]


def test_set_dependency_empty_key_raises(vault_path):
    with pytest.raises(ValueError, match="key must not be empty"):
        set_dependency(vault_path, "", ["OTHER"])


def test_set_dependency_empty_depends_on_raises(vault_path):
    with pytest.raises(ValueError, match="depends_on must not be empty"):
        set_dependency(vault_path, "A", [])


def test_set_dependency_self_reference_raises(vault_path):
    with pytest.raises(ValueError, match="cannot depend on itself"):
        set_dependency(vault_path, "A", ["A"])


def test_remove_dependency_returns_true_when_removed(vault_path):
    set_dependency(vault_path, "X", ["Y"])
    assert remove_dependency(vault_path, "X") is True
    assert load_dependencies(vault_path) == {}


def test_remove_dependency_returns_false_when_absent(vault_path):
    assert remove_dependency(vault_path, "MISSING") is False


def test_get_dependents_reverse_lookup(vault_path):
    set_dependency(vault_path, "APP_URL", ["HOST", "PORT"])
    set_dependency(vault_path, "REDIRECT", ["HOST"])
    dependents = get_dependents(vault_path, "HOST")
    assert "APP_URL" in dependents
    assert "REDIRECT" in dependents


def test_get_dependents_empty_when_none(vault_path):
    set_dependency(vault_path, "A", ["B"])
    assert get_dependents(vault_path, "C") == []


def test_resolve_order_deps_come_first(vault_path):
    set_dependency(vault_path, "C", ["B"])
    set_dependency(vault_path, "B", ["A"])
    order = resolve_order(vault_path, ["C", "B", "A"])
    assert order.index("A") < order.index("B")
    assert order.index("B") < order.index("C")


def test_resolve_order_cycle_raises(vault_path):
    save_dependencies(vault_path, {"A": ["B"], "B": ["A"]})
    with pytest.raises(ValueError, match="Circular dependency"):
        resolve_order(vault_path, ["A", "B"])


def test_sidecar_is_valid_json(vault_path):
    set_dependency(vault_path, "KEY", ["OTHER"])
    raw = _deps_path(vault_path).read_text()
    data = json.loads(raw)
    assert isinstance(data, dict)
