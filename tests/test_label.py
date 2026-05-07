"""Tests for envault.label."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.label import (
    _labels_path,
    load_labels,
    save_labels,
    get_labels,
    set_labels,
    add_label,
    remove_label,
    keys_by_label,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "test.vault"


def test_sidecar_uses_labels_suffix(vault_path: Path) -> None:
    assert str(_labels_path(vault_path)).endswith(".labels.json")


def test_sidecar_not_created_until_first_set(vault_path: Path) -> None:
    _ = load_labels(vault_path)
    assert not _labels_path(vault_path).exists()


def test_load_labels_returns_empty_when_no_file(vault_path: Path) -> None:
    assert load_labels(vault_path) == {}


def test_set_labels_persists(vault_path: Path) -> None:
    set_labels(vault_path, "API_KEY", ["secret", "prod"])
    assert get_labels(vault_path, "API_KEY") == ["secret", "prod"]


def test_set_labels_deduplicates(vault_path: Path) -> None:
    set_labels(vault_path, "DB_URL", ["infra", "infra", "prod"])
    assert get_labels(vault_path, "DB_URL") == ["infra", "prod"]


def test_set_labels_empty_list_removes_entry(vault_path: Path) -> None:
    set_labels(vault_path, "TOKEN", ["ci"])
    set_labels(vault_path, "TOKEN", [])
    assert get_labels(vault_path, "TOKEN") == []
    assert "TOKEN" not in load_labels(vault_path)


def test_set_labels_empty_key_raises(vault_path: Path) -> None:
    with pytest.raises(ValueError, match="key"):
        set_labels(vault_path, "", ["tag"])


def test_get_labels_returns_empty_for_untagged_key(vault_path: Path) -> None:
    assert get_labels(vault_path, "MISSING") == []


def test_add_label_appends(vault_path: Path) -> None:
    add_label(vault_path, "API_KEY", "secret")
    add_label(vault_path, "API_KEY", "prod")
    assert get_labels(vault_path, "API_KEY") == ["secret", "prod"]


def test_add_label_no_duplicates(vault_path: Path) -> None:
    add_label(vault_path, "API_KEY", "secret")
    add_label(vault_path, "API_KEY", "secret")
    assert get_labels(vault_path, "API_KEY").count("secret") == 1


def test_add_label_empty_raises(vault_path: Path) -> None:
    with pytest.raises(ValueError, match="label"):
        add_label(vault_path, "KEY", "")


def test_remove_label_returns_true_when_removed(vault_path: Path) -> None:
    set_labels(vault_path, "KEY", ["a", "b"])
    assert remove_label(vault_path, "KEY", "a") is True
    assert get_labels(vault_path, "KEY") == ["b"]


def test_remove_label_returns_false_when_absent(vault_path: Path) -> None:
    assert remove_label(vault_path, "KEY", "nonexistent") is False


def test_keys_by_label_returns_sorted(vault_path: Path) -> None:
    set_labels(vault_path, "Z_KEY", ["shared"])
    set_labels(vault_path, "A_KEY", ["shared"])
    set_labels(vault_path, "M_KEY", ["other"])
    assert keys_by_label(vault_path, "shared") == ["A_KEY", "Z_KEY"]


def test_sidecar_is_valid_json(vault_path: Path) -> None:
    set_labels(vault_path, "KEY", ["x"])
    raw = _labels_path(vault_path).read_text(encoding="utf-8")
    data = json.loads(raw)
    assert isinstance(data, dict)
