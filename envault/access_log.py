"""Per-key access log: records every get/set/delete operation with timestamps."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional


def _access_log_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".access_log.json")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_access_log(vault_path: Path) -> List[Dict[str, Any]]:
    """Return all access log entries, or an empty list if none exist."""
    path = _access_log_path(vault_path)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_access_log(vault_path: Path, entries: List[Dict[str, Any]]) -> None:
    path = _access_log_path(vault_path)
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def record_access(
    vault_path: Path,
    operation: str,
    key: str,
    actor: Optional[str] = None,
) -> None:
    """Append a single access entry for *key* and *operation*.

    Args:
        vault_path: Path to the vault file (sidecar is placed alongside it).
        operation:  One of ``'get'``, ``'set'``, ``'delete'``.
        key:        The vault key that was accessed.
        actor:      Optional free-form identifier for who performed the action.
    """
    valid_ops = {"get", "set", "delete"}
    if operation not in valid_ops:
        raise ValueError(f"operation must be one of {valid_ops}, got {operation!r}")
    if not key:
        raise ValueError("key must not be empty")

    entries = load_access_log(vault_path)
    entry: Dict[str, Any] = {
        "timestamp": _now_utc(),
        "operation": operation,
        "key": key,
    }
    if actor is not None:
        entry["actor"] = actor
    entries.append(entry)
    save_access_log(vault_path, entries)


def get_key_history(
    vault_path: Path, key: str
) -> List[Dict[str, Any]]:
    """Return all access log entries for a specific *key*."""
    return [e for e in load_access_log(vault_path) if e.get("key") == key]


def clear_access_log(vault_path: Path) -> None:
    """Remove all entries from the access log."""
    path = _access_log_path(vault_path)
    if path.exists():
        path.unlink()
