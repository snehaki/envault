"""Tests for envault.reminder."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envault.reminder import (
    ReminderStatus,
    check_reminders,
    load_reminders,
    remove_reminder,
    set_reminder,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "test.vault"


def test_set_reminder_persists(vault_path: Path) -> None:
    set_reminder(vault_path, "DB_PASSWORD", 30)
    data = load_reminders(vault_path)
    assert "DB_PASSWORD" in data
    assert data["DB_PASSWORD"]["rotate_after_days"] == 30


def test_set_reminder_raises_for_non_positive_days(vault_path: Path) -> None:
    with pytest.raises(ValueError):
        set_reminder(vault_path, "KEY", 0)
    with pytest.raises(ValueError):
        set_reminder(vault_path, "KEY", -5)


def test_load_reminders_returns_empty_when_no_file(vault_path: Path) -> None:
    assert load_reminders(vault_path) == {}


def test_remove_reminder_returns_true_when_removed(vault_path: Path) -> None:
    set_reminder(vault_path, "API_KEY", 14)
    assert remove_reminder(vault_path, "API_KEY") is True
    assert "API_KEY" not in load_reminders(vault_path)


def test_remove_reminder_returns_false_when_not_present(vault_path: Path) -> None:
    assert remove_reminder(vault_path, "MISSING") is False


def test_check_reminders_returns_overdue_keys(vault_path: Path, monkeypatch) -> None:
    import envault.reminder as mod

    past = datetime.now(timezone.utc) - timedelta(days=40)

    def _fake_now():
        return datetime.now(timezone.utc)

    # Manually write an old set_at so the key is overdue
    from envault.reminder import save_reminders
    save_reminders(vault_path, {
        "OLD_KEY": {"rotate_after_days": 30, "set_at": past.isoformat()},
    })

    results = check_reminders(vault_path, warn_days=7)
    assert len(results) == 1
    assert results[0].key == "OLD_KEY"
    assert results[0].overdue is True


def test_check_reminders_returns_soon_due_keys(vault_path: Path) -> None:
    from envault.reminder import save_reminders
    # Key set 25 days ago with 30-day rotation → 5 days remaining → within warn_days=7
    past = datetime.now(timezone.utc) - timedelta(days=25)
    save_reminders(vault_path, {
        "SOON_KEY": {"rotate_after_days": 30, "set_at": past.isoformat()},
    })
    results = check_reminders(vault_path, warn_days=7)
    assert any(r.key == "SOON_KEY" for r in results)
    match = next(r for r in results if r.key == "SOON_KEY")
    assert match.overdue is False


def test_check_reminders_excludes_fresh_keys(vault_path: Path) -> None:
    set_reminder(vault_path, "FRESH_KEY", 90)
    results = check_reminders(vault_path, warn_days=7)
    assert all(r.key != "FRESH_KEY" for r in results)


def test_check_reminders_sorted_by_due_date(vault_path: Path) -> None:
    from envault.reminder import save_reminders
    now = datetime.now(timezone.utc)
    save_reminders(vault_path, {
        "B": {"rotate_after_days": 1, "set_at": (now - timedelta(days=5)).isoformat()},
        "A": {"rotate_after_days": 1, "set_at": (now - timedelta(days=10)).isoformat()},
    })
    results = check_reminders(vault_path, warn_days=30)
    assert results[0].key == "A"
    assert results[1].key == "B"
