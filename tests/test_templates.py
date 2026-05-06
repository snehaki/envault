"""Tests for envault.templates module."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.templates import (
    create_template,
    delete_template,
    list_templates,
    load_templates,
    apply_template,
    _templates_path,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    vp = tmp_path / ".envault"
    vp.write_text(json.dumps({"keys": {}}))
    return vp


def _make_vault_with_keys(vault_path: Path, keys: list[str]) -> dict:
    vault = {"keys": {k: "encrypted_value" for k in keys}}
    vault_path.write_text(json.dumps(vault))
    return vault


def test_templates_file_not_created_until_first_save(vault_path: Path) -> None:
    assert not _templates_path(vault_path).exists()


def test_load_templates_returns_empty_when_no_file(vault_path: Path) -> None:
    assert load_templates(vault_path) == {}


def test_create_template_persists(vault_path: Path) -> None:
    create_template(vault_path, "backend", ["DB_HOST", "DB_PASS"])
    templates = load_templates(vault_path)
    assert "backend" in templates
    assert templates["backend"] == ["DB_HOST", "DB_PASS"]


def test_create_template_deduplicates_keys(vault_path: Path) -> None:
    create_template(vault_path, "dup", ["KEY_A", "KEY_A", "KEY_B"])
    assert load_templates(vault_path)["dup"] == ["KEY_A", "KEY_B"]


def test_create_template_overwrites_existing(vault_path: Path) -> None:
    create_template(vault_path, "t", ["OLD"])
    create_template(vault_path, "t", ["NEW"])
    assert load_templates(vault_path)["t"] == ["NEW"]


def test_create_template_raises_for_empty_name(vault_path: Path) -> None:
    with pytest.raises(ValueError, match="empty"):
        create_template(vault_path, "", ["KEY"])


def test_create_template_raises_for_empty_keys(vault_path: Path) -> None:
    with pytest.raises(ValueError, match="at least one key"):
        create_template(vault_path, "empty", [])


def test_list_templates_sorted(vault_path: Path) -> None:
    create_template(vault_path, "zebra", ["Z"])
    create_template(vault_path, "alpha", ["A"])
    assert list_templates(vault_path) == ["alpha", "zebra"]


def test_delete_template_removes_entry(vault_path: Path) -> None:
    create_template(vault_path, "to_delete", ["X"])
    delete_template(vault_path, "to_delete")
    assert "to_delete" not in load_templates(vault_path)


def test_delete_template_raises_when_not_found(vault_path: Path) -> None:
    with pytest.raises(KeyError, match="ghost"):
        delete_template(vault_path, "ghost")


def test_apply_template_returns_present_keys(vault_path: Path) -> None:
    vault = _make_vault_with_keys(vault_path, ["DB_HOST", "DB_PASS", "OTHER"])
    create_template(vault_path, "db", ["DB_HOST", "DB_PASS", "MISSING_KEY"])
    present = apply_template(vault_path, "db", vault, passphrase="secret")
    assert sorted(present) == ["DB_HOST", "DB_PASS"]


def test_apply_template_raises_when_template_not_found(vault_path: Path) -> None:
    with pytest.raises(KeyError, match="nope"):
        apply_template(vault_path, "nope", {"keys": {}}, passphrase="x")
