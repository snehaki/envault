"""Sidecar file behaviour tests for envault.pin."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from envault.pin import set_pin, remove_pin, _pins_path, load_pins


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "project.vault")


def test_sidecar_uses_pins_suffix(vault_path: str) -> None:
    p = _pins_path(vault_path)
    assert p.name == "project.pins.json"


def test_sidecar_not_created_until_first_set(vault_path: str) -> None:
    _ = load_pins(vault_path)  # read without writing
    assert not _pins_path(vault_path).exists()


def test_sidecar_created_after_set(vault_path: str) -> None:
    set_pin(vault_path, "TOKEN", "pass1")
    assert _pins_path(vault_path).exists()


def test_sidecar_is_valid_json(vault_path: str) -> None:
    set_pin(vault_path, "TOKEN", "pass1")
    data = json.loads(_pins_path(vault_path).read_text())
    assert isinstance(data, dict)


def test_sidecar_stores_hash_not_plaintext(vault_path: str) -> None:
    set_pin(vault_path, "TOKEN", "mysecretpin")
    data = json.loads(_pins_path(vault_path).read_text())
    assert data["TOKEN"] != "mysecretpin"
    assert len(data["TOKEN"]) == 64  # SHA-256 hex digest


def test_sidecar_removed_entry_disappears(vault_path: str) -> None:
    set_pin(vault_path, "A", "1234")
    set_pin(vault_path, "B", "5678")
    remove_pin(vault_path, "A")
    data = json.loads(_pins_path(vault_path).read_text())
    assert "A" not in data
    assert "B" in data
