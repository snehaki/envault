"""TTL (time-to-live) support for vault keys.

Stores expiry timestamps in a sidecar metadata section of the vault
under the top-level key ``_ttl``.  All timestamps are UTC ISO-8601.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

_TTL_SECTION = "_ttl"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def set_ttl(vault: dict, key: str, seconds: int) -> None:
    """Set an expiry for *key* that is *seconds* from now."""
    if seconds <= 0:
        raise ValueError("TTL must be a positive number of seconds.")
    expiry = _now_utc() + timedelta(seconds=seconds)
    vault.setdefault(_TTL_SECTION, {})[key] = expiry.isoformat()


def get_ttl(vault: dict, key: str) -> Optional[datetime]:
    """Return the expiry datetime for *key*, or None if no TTL is set."""
    raw = vault.get(_TTL_SECTION, {}).get(key)
    if raw is None:
        return None
    return datetime.fromisoformat(raw)


def remove_ttl(vault: dict, key: str) -> None:
    """Remove the TTL for *key* if present."""
    section = vault.get(_TTL_SECTION, {})
    section.pop(key, None)
    if not section:
        vault.pop(_TTL_SECTION, None)


def is_expired(vault: dict, key: str) -> bool:
    """Return True if *key* has a TTL that has already passed."""
    expiry = get_ttl(vault, key)
    if expiry is None:
        return False
    return _now_utc() >= expiry


def purge_expired(vault: dict) -> list[str]:
    """Delete all vault entries whose TTL has expired.

    Returns the list of keys that were removed.
    """
    expired = [
        k for k in list(vault.get(_TTL_SECTION, {}).keys())
        if is_expired(vault, k)
    ]
    for key in expired:
        vault.pop(key, None)
        remove_ttl(vault, key)
    return expired


def list_ttls(vault: dict) -> dict[str, datetime]:
    """Return a mapping of key -> expiry datetime for all keys with a TTL."""
    return {
        k: datetime.fromisoformat(v)
        for k, v in vault.get(_TTL_SECTION, {}).items()
    }
