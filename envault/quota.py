"""Per-vault key quota enforcement."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

_SIDECAR_SUFFIX = ".quotas"
_DEFAULT_LIMIT = 100


def _quota_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(_SIDECAR_SUFFIX)


def load_quota(vault_path: Path) -> dict:
    p = _quota_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def save_quota(vault_path: Path, data: dict) -> None:
    _quota_path(vault_path).write_text(json.dumps(data, indent=2))


def set_limit(vault_path: Path, limit: int) -> None:
    """Set the maximum number of keys allowed in this vault."""
    if limit < 1:
        raise ValueError("limit must be a positive integer")
    data = load_quota(vault_path)
    data["limit"] = limit
    save_quota(vault_path, data)


def get_limit(vault_path: Path) -> int:
    """Return the configured limit, or the default if not set."""
    data = load_quota(vault_path)
    return int(data.get("limit", _DEFAULT_LIMIT))


def remove_limit(vault_path: Path) -> bool:
    """Remove the quota limit. Returns True if a limit existed."""
    data = load_quota(vault_path)
    if "limit" not in data:
        return False
    del data["limit"]
    save_quota(vault_path, data)
    return True


def check_quota(vault_path: Path, current_key_count: int) -> Optional[str]:
    """Return an error message if the quota would be exceeded, else None."""
    limit = get_limit(vault_path)
    if current_key_count >= limit:
        return f"Key quota exceeded: {current_key_count}/{limit} keys used."
    return None
