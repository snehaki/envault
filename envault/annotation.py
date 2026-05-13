"""Per-key annotation (freeform description/notes) sidecar for envault vaults."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


def _annotations_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".annotations.json")


def load_annotations(vault_path: str) -> Dict[str, str]:
    """Return mapping of key -> annotation text, or empty dict if no sidecar."""
    path = _annotations_path(vault_path)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, str)}


def save_annotations(vault_path: str, annotations: Dict[str, str]) -> None:
    """Persist annotations dict to the sidecar file."""
    path = _annotations_path(vault_path)
    path.write_text(json.dumps(annotations, indent=2, sort_keys=True), encoding="utf-8")


def set_annotation(vault_path: str, key: str, text: str) -> None:
    """Set or update the annotation for *key*."""
    if not key:
        raise ValueError("key must not be empty")
    annotations = load_annotations(vault_path)
    annotations[key] = text
    save_annotations(vault_path, annotations)


def remove_annotation(vault_path: str, key: str) -> bool:
    """Remove the annotation for *key*. Returns True if it existed."""
    annotations = load_annotations(vault_path)
    if key not in annotations:
        return False
    del annotations[key]
    save_annotations(vault_path, annotations)
    return True


def get_annotation(vault_path: str, key: str) -> str | None:
    """Return annotation text for *key*, or None if not set."""
    return load_annotations(vault_path).get(key)


def list_annotations(vault_path: str) -> Dict[str, str]:
    """Return all key -> annotation mappings, sorted by key."""
    return dict(sorted(load_annotations(vault_path).items()))
