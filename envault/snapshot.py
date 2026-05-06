"""Vault snapshot management — save/load key-only snapshots for diffing."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_SNAPSHOT_NAME = ".envault.snapshot"


def snapshot_path(vault_path: Path) -> Path:
    """Return the snapshot file path adjacent to *vault_path*."""
    return vault_path.parent / DEFAULT_SNAPSHOT_NAME


def save_snapshot(vault: Dict[str, str], path: Path) -> None:
    """Persist a sorted list of key names to *path* (JSON, no secrets)."""
    keys = sorted(vault.keys())
    path.write_text(json.dumps(keys, indent=2) + "\n", encoding="utf-8")


def load_snapshot(path: Path) -> List[str]:
    """Load a previously saved snapshot; returns [] if file is missing."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Corrupt snapshot at {path}: invalid JSON — {exc}") from exc
    if not isinstance(data, list):
        raise ValueError(f"Corrupt snapshot at {path}: expected a JSON list")
    if not all(isinstance(k, str) for k in data):
        raise ValueError(f"Corrupt snapshot at {path}: all entries must be strings")
    return data


def snapshot_diff_summary(
    old_keys: List[str],
    new_vault: Dict[str, str],
) -> str:
    """Return a human-readable diff between *old_keys* and *new_vault* keys."""
    from envault.diff import VaultDiff  # local import to avoid circular

    old_set = set(old_keys)
    new_set = set(new_vault.keys())
    diff = VaultDiff(
        added=sorted(new_set - old_set),
        removed=sorted(old_set - new_set),
        changed=[],  # key-only snapshot cannot detect value changes
    )
    return diff.summary()
