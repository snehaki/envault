"""Read-only lock management for vault keys.

Allows individual keys to be marked as read-only, preventing
accidental overwrites via `envault set`.
"""

from __future__ import annotations

import json
from pathlib import Path

VAULT_READONLY_SUFFIX = ".readonly.json"


def _readonly_path(vault_path: str | Path) -> Path:
    return Path(str(vault_path) + VAULT_READONLY_SUFFIX)


def load_readonly(vault_path: str | Path) -> set[str]:
    """Return the set of keys marked read-only for *vault_path*."""
    p = _readonly_path(vault_path)
    if not p.exists():
        return set()
    data = json.loads(p.read_text())
    if not isinstance(data, list):
        return set()
    return set(data)


def save_readonly(vault_path: str | Path, keys: set[str]) -> None:
    """Persist the set of read-only *keys* for *vault_path*."""
    p = _readonly_path(vault_path)
    p.write_text(json.dumps(sorted(keys), indent=2))


def lock_key(vault_path: str | Path, key: str) -> None:
    """Mark *key* as read-only.  Raises ValueError for empty key."""
    if not key:
        raise ValueError("key must not be empty")
    keys = load_readonly(vault_path)
    keys.add(key)
    save_readonly(vault_path, keys)


def unlock_key(vault_path: str | Path, key: str) -> bool:
    """Remove the read-only lock from *key*.

    Returns True if the key was locked, False if it was not.
    """
    keys = load_readonly(vault_path)
    if key not in keys:
        return False
    keys.discard(key)
    save_readonly(vault_path, keys)
    return True


def is_locked(vault_path: str | Path, key: str) -> bool:
    """Return True if *key* is marked read-only."""
    return key in load_readonly(vault_path)


def list_locked(vault_path: str | Path) -> list[str]:
    """Return a sorted list of all read-only keys."""
    return sorted(load_readonly(vault_path))
