"""Priority levels for vault keys."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

VALID_PRIORITIES = {"low", "medium", "high", "critical"}
DEFAULT_PRIORITY = "medium"


def _priority_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".priorities.json")


def load_priorities(vault_path: Path) -> Dict[str, str]:
    """Load priority map from sidecar file."""
    p = _priority_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def save_priorities(vault_path: Path, priorities: Dict[str, str]) -> None:
    """Persist priority map to sidecar file."""
    _priority_path(vault_path).write_text(json.dumps(priorities, indent=2))


def set_priority(vault_path: Path, key: str, level: str) -> None:
    """Assign a priority level to a key."""
    if not key:
        raise ValueError("Key must not be empty.")
    level = level.lower()
    if level not in VALID_PRIORITIES:
        raise ValueError(
            f"Invalid priority '{level}'. Choose from: {sorted(VALID_PRIORITIES)}."
        )
    priorities = load_priorities(vault_path)
    priorities[key] = level
    save_priorities(vault_path, priorities)


def remove_priority(vault_path: Path, key: str) -> bool:
    """Remove priority for a key. Returns True if it existed."""
    priorities = load_priorities(vault_path)
    if key in priorities:
        del priorities[key]
        save_priorities(vault_path, priorities)
        return True
    return False


def get_priority(vault_path: Path, key: str) -> str:
    """Return the priority level for a key, or the default."""
    return load_priorities(vault_path).get(key, DEFAULT_PRIORITY)


def keys_by_priority(vault_path: Path, level: str) -> list[str]:
    """Return all keys assigned to a given priority level."""
    level = level.lower()
    return sorted(k for k, v in load_priorities(vault_path).items() if v == level)
