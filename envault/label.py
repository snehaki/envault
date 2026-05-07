"""Per-key labels (free-form metadata strings) stored in a sidecar file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def _labels_path(vault_path: str | Path) -> Path:
    return Path(str(vault_path) + ".labels.json")


def load_labels(vault_path: str | Path) -> Dict[str, List[str]]:
    """Return mapping of key -> list[label].  Empty dict when no sidecar exists."""
    p = _labels_path(vault_path)
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return {k: list(v) for k, v in data.items() if isinstance(v, list)}


def save_labels(vault_path: str | Path, labels: Dict[str, List[str]]) -> None:
    """Persist the labels mapping to the sidecar file."""
    p = _labels_path(vault_path)
    p.write_text(json.dumps(labels, indent=2, sort_keys=True), encoding="utf-8")


def get_labels(vault_path: str | Path, key: str) -> List[str]:
    """Return labels assigned to *key*, or an empty list."""
    return load_labels(vault_path).get(key, [])


def set_labels(vault_path: str | Path, key: str, labels: List[str]) -> None:
    """Replace the label list for *key*.  Removes entry when list is empty."""
    if not key:
        raise ValueError("key must not be empty")
    data = load_labels(vault_path)
    deduped = list(dict.fromkeys(labels))  # preserve order, remove duplicates
    if deduped:
        data[key] = deduped
    else:
        data.pop(key, None)
    save_labels(vault_path, data)


def add_label(vault_path: str | Path, key: str, label: str) -> None:
    """Add *label* to *key* if not already present."""
    if not label:
        raise ValueError("label must not be empty")
    current = get_labels(vault_path, key)
    if label not in current:
        set_labels(vault_path, key, current + [label])


def remove_label(vault_path: str | Path, key: str, label: str) -> bool:
    """Remove *label* from *key*.  Returns True if it was present."""
    current = get_labels(vault_path, key)
    if label not in current:
        return False
    set_labels(vault_path, key, [l for l in current if l != label])
    return True


def keys_by_label(vault_path: str | Path, label: str) -> List[str]:
    """Return sorted list of keys that carry *label*."""
    return sorted(k for k, v in load_labels(vault_path).items() if label in v)
