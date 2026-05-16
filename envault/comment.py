"""Per-key inline comments stored in a sidecar JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


def _comments_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".comments.json")


def load_comments(vault_path: str) -> Dict[str, str]:
    """Return mapping of key -> comment string."""
    p = _comments_path(vault_path)
    if not p.exists():
        return {}
    data = json.loads(p.read_text())
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, str)}


def save_comments(vault_path: str, comments: Dict[str, str]) -> None:
    """Persist comments mapping to the sidecar file."""
    p = _comments_path(vault_path)
    p.write_text(json.dumps(comments, indent=2, sort_keys=True))


def set_comment(vault_path: str, key: str, comment: str) -> None:
    """Set or replace the comment for *key*."""
    if not key:
        raise ValueError("key must not be empty")
    if not comment:
        raise ValueError("comment must not be empty")
    comments = load_comments(vault_path)
    comments[key] = comment
    save_comments(vault_path, comments)


def remove_comment(vault_path: str, key: str) -> bool:
    """Remove the comment for *key*. Returns True if it existed."""
    comments = load_comments(vault_path)
    if key not in comments:
        return False
    del comments[key]
    save_comments(vault_path, comments)
    return True


def get_comment(vault_path: str, key: str) -> Optional[str]:
    """Return the comment for *key*, or None if not set."""
    return load_comments(vault_path).get(key)


def all_comments(vault_path: str) -> Dict[str, str]:
    """Return all key->comment pairs (alias for load_comments)."""
    return load_comments(vault_path)
