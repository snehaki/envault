"""Reminder / rotation-due tracking for vault keys.

Each key can have a 'rotate_after_days' policy stored in a sidecar JSON file.
When a key is set (or its reminder is configured), the current UTC timestamp
is recorded as the baseline.  `check_reminders` returns every key whose
rotation deadline has passed or is within `warn_days` days.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import NamedTuple


def _reminders_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".reminders.json")


def load_reminders(vault_path: Path) -> dict:
    p = _reminders_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def save_reminders(vault_path: Path, data: dict) -> None:
    _reminders_path(vault_path).write_text(json.dumps(data, indent=2))


def set_reminder(vault_path: Path, key: str, rotate_after_days: int) -> None:
    if rotate_after_days <= 0:
        raise ValueError("rotate_after_days must be a positive integer")
    data = load_reminders(vault_path)
    data[key] = {
        "rotate_after_days": rotate_after_days,
        "set_at": datetime.now(timezone.utc).isoformat(),
    }
    save_reminders(vault_path, data)


def remove_reminder(vault_path: Path, key: str) -> bool:
    data = load_reminders(vault_path)
    if key not in data:
        return False
    del data[key]
    save_reminders(vault_path, data)
    return True


class ReminderStatus(NamedTuple):
    key: str
    rotate_after_days: int
    set_at: datetime
    due_date: datetime
    overdue: bool
    days_remaining: int


def check_reminders(vault_path: Path, warn_days: int = 7) -> list[ReminderStatus]:
    """Return keys that are overdue or due within *warn_days* days."""
    data = load_reminders(vault_path)
    now = datetime.now(timezone.utc)
    results: list[ReminderStatus] = []
    for key, entry in data.items():
        set_at = datetime.fromisoformat(entry["set_at"])
        rotate_after = entry["rotate_after_days"]
        due = set_at + timedelta(days=rotate_after)
        remaining = (due - now).days
        if remaining <= warn_days:
            results.append(
                ReminderStatus(
                    key=key,
                    rotate_after_days=rotate_after,
                    set_at=set_at,
                    due_date=due,
                    overdue=now >= due,
                    days_remaining=remaining,
                )
            )
    return sorted(results, key=lambda r: r.due_date)
