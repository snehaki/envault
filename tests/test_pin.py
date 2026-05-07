"""Unit tests for envault.pin."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from envault.pin import (
    set_pin,
    remove_pin,
    verify_pin,
    is_pinned,
    pinned_keys,
    load_pins,
    _pins_path,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.vault")


def test_sidecar_uses_pins_suffix(vault_path: str) -> None:
    assert str(_pins_path(vault_path)).endswith(".pins.json")


def test_sidecar_not_created_until_first_set(vault_path: str, tmp_path: Path) -> None:
    assert not _pins_path(vault_path).exists()


def test_set_pin_persists(vault_path: str) -> None:
    set_pin(vault_path, "SECRET", "1234")
    assert is_pinned(vault_path, "SECRET")


def test_set_pin_sidecar_is_valid_json(vault_path: str) -> None:
    set_pin(vault_path, "KEY", "abcd")
    data = json.loads(_pins_path(vault_path).read_text())
    assert "KEY" in data


def test_set_pin_raises_for_empty_pin(vault_path: str) -> None:
    with pytest.raises(ValueError, match="empty"):
        set_pin(vault_path, "KEY", "")


def test_set_pin_raises_for_short_pin(vault_path: str) -> None:
    with pytest.raises(ValueError, match="4 characters"):
        set_pin(vault_path, "KEY", "12")


def test_verify_pin_correct(vault_path: str) -> None:
    set_pin(vault_path, "KEY", "securepin")
    assert verify_pin(vault_path, "KEY", "securepin") is True


def test_verify_pin_wrong(vault_path: str) -> None:
    set_pin(vault_path, "KEY", "securepin")
    assert verify_pin(vault_path, "KEY", "wrongpin") is False


def test_verify_pin_no_pin_set_returns_true(vault_path: str) -> None:
    """Keys without a PIN should always be accessible."""
    assert verify_pin(vault_path, "UNPROTECTED", "anything") is True


def test_remove_pin_returns_true_when_existed(vault_path: str) -> None:
    set_pin(vault_path, "KEY", "1234")
    assert remove_pin(vault_path, "KEY") is True


def test_remove_pin_returns_false_when_not_set(vault_path: str) -> None:
    assert remove_pin(vault_path, "GHOST") is False


def test_remove_pin_clears_entry(vault_path: str) -> None:
    set_pin(vault_path, "KEY", "1234")
    remove_pin(vault_path, "KEY")
    assert not is_pinned(vault_path, "KEY")


def test_pinned_keys_sorted(vault_path: str) -> None:
    set_pin(vault_path, "ZEBRA", "1234")
    set_pin(vault_path, "ALPHA", "1234")
    set_pin(vault_path, "MANGO", "1234")
    assert pinned_keys(vault_path) == ["ALPHA", "MANGO", "ZEBRA"]


def test_load_pins_returns_empty_when_no_file(vault_path: str) -> None:
    assert load_pins(vault_path) == {}
