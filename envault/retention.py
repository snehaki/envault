"""Retention policy sidecar: auto-delete vault keys after N days of inactivity."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional


def _retention_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".retention.json")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def load_retention(vault_path: str) -> Dict[str, int]:
    """Return mapping of key -> retention days. Empty dict if no sidecar."""
    path = _retention_path(vault_path)
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return {k: int(v) for k, v in data.items() if isinstance(v, (int, float))}


def save_retention(vault_path: str, mapping: Dict[str, int]) -> None:
    path = _retention_path(vault_path)
    path.write_text(json.dumps(mapping, indent=2, sort_keys=True))


def set_retention(vault_path: str, key: str, days: int) -> None:
    """Set retention period (in days) for *key*. Must be positive."""
    if days <= 0:
        raise ValueError("Retention days must be a positive integer.")
    mapping = load_retention(vault_path)
    mapping[key] = days
    save_retention(vault_path, mapping)


def remove_retention(vault_path: str, key: str) -> bool:
    """Remove retention rule for *key*. Returns True if entry existed."""
    mapping = load_retention(vault_path)
    if key not in mapping:
        return False
    del mapping[key]
    save_retention(vault_path, mapping)
    return True


def expired_keys(
    vault_path: str,
    last_accessed: Dict[str, datetime],
) -> List[str]:
    """Return keys whose retention period has elapsed since last access.

    *last_accessed* maps key -> last-access datetime (UTC-aware).
    Keys without a last-access entry are treated as accessed at epoch.
    """
    mapping = load_retention(vault_path)
    now = _now_utc()
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    result: List[str] = []
    for key, days in mapping.items():
        last = last_accessed.get(key, epoch)
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if now - last >= timedelta(days=days):
            result.append(key)
    return sorted(result)
