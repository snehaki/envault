"""Tests for the sidecar file naming and isolation of reminder storage."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.reminder import (
    _reminders_path,
    load_reminders,
    set_reminder,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "project.vault"


def test_sidecar_uses_reminders_suffix(vault_path: Path) -> None:
    sidecar = _reminders_path(vault_path)
    assert sidecar.name == "project.reminders.json"
    assert sidecar.parent == vault_path.parent


def test_sidecar_not_created_until_first_set(vault_path: Path) -> None:
    sidecar = _reminders_path(vault_path)
    assert not sidecar.exists()
    load_reminders(vault_path)  # read-only, should not create file
    assert not sidecar.exists()


def test_sidecar_created_after_set(vault_path: Path) -> None:
    sidecar = _reminders_path(vault_path)
    set_reminder(vault_path, "KEY", 10)
    assert sidecar.exists()


def test_sidecar_is_valid_json(vault_path: Path) -> None:
    import json
    set_reminder(vault_path, "ALPHA", 7)
    set_reminder(vault_path, "BETA", 14)
    sidecar = _reminders_path(vault_path)
    data = json.loads(sidecar.read_text())
    assert "ALPHA" in data
    assert "BETA" in data


def test_multiple_vaults_have_independent_sidecars(tmp_path: Path) -> None:
    vault_a = tmp_path / "a.vault"
    vault_b = tmp_path / "b.vault"
    set_reminder(vault_a, "KEY_A", 5)
    set_reminder(vault_b, "KEY_B", 10)
    data_a = load_reminders(vault_a)
    data_b = load_reminders(vault_b)
    assert "KEY_A" in data_a and "KEY_B" not in data_a
    assert "KEY_B" in data_b and "KEY_A" not in data_b


def test_overwrite_reminder_updates_days(vault_path: Path) -> None:
    set_reminder(vault_path, "SECRET", 30)
    set_reminder(vault_path, "SECRET", 60)
    data = load_reminders(vault_path)
    assert data["SECRET"]["rotate_after_days"] == 60
