"""Key expiry management — set, check, and list expiring vault keys."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _expiry_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".expiry.json")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def load_expiry(vault_path: str) -> dict:
    p = _expiry_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def save_expiry(vault_path: str, data: dict) -> None:
    _expiry_path(vault_path).write_text(json.dumps(data, indent=2))


def set_expiry(vault_path: str, key: str, days: int) -> datetime:
    """Set expiry for *key* to *days* days from now. Returns the expiry datetime."""
    if days <= 0:
        raise ValueError("days must be a positive integer")
    data = load_expiry(vault_path)
    expires_at = _now_utc().replace(microsecond=0)
    from datetime import timedelta
    expires_at = expires_at + timedelta(days=days)
    data[key] = expires_at.isoformat()
    save_expiry(vault_path, data)
    return expires_at


def remove_expiry(vault_path: str, key: str) -> bool:
    data = load_expiry(vault_path)
    if key not in data:
        return False
    del data[key]
    save_expiry(vault_path, data)
    return True


def get_expiry(vault_path: str, key: str) -> Optional[datetime]:
    data = load_expiry(vault_path)
    if key not in data:
        return None
    return datetime.fromisoformat(data[key])


def is_expired(vault_path: str, key: str) -> bool:
    exp = get_expiry(vault_path, key)
    if exp is None:
        return False
    return _now_utc() >= exp


def list_expiring(vault_path: str) -> list[dict]:
    """Return all keys with expiry info, sorted by expiry date."""
    data = load_expiry(vault_path)
    now = _now_utc()
    result = []
    for key, iso in data.items():
        exp = datetime.fromisoformat(iso)
        result.append({"key": key, "expires_at": exp, "expired": now >= exp})
    result.sort(key=lambda r: r["expires_at"])
    return result
