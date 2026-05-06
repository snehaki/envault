"""Key renaming / import-map support for envault.

An import-map is a JSON sidecar (<vault>.importmap.json) that stores
a mapping of  source_key -> target_key  used when importing .env files
so that external variable names can be translated to project-internal names.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


# ---------------------------------------------------------------------------
# Sidecar helpers
# ---------------------------------------------------------------------------

def _map_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".importmap.json")


def load_map(vault_path: Path) -> Dict[str, str]:
    """Return the import-map for *vault_path*, or an empty dict."""
    p = _map_path(vault_path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def save_map(vault_path: Path, mapping: Dict[str, str]) -> None:
    """Persist *mapping* as the import-map sidecar for *vault_path*."""
    p = _map_path(vault_path)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(mapping, fh, indent=2, sort_keys=True)


def set_entry(vault_path: Path, source_key: str, target_key: str) -> None:
    """Add or update a single source->target mapping."""
    if not source_key:
        raise ValueError("source_key must not be empty")
    if not target_key:
        raise ValueError("target_key must not be empty")
    mapping = load_map(vault_path)
    mapping[source_key] = target_key
    save_map(vault_path, mapping)


def remove_entry(vault_path: Path, source_key: str) -> bool:
    """Remove a mapping; return True if it existed."""
    mapping = load_map(vault_path)
    if source_key not in mapping:
        return False
    del mapping[source_key]
    save_map(vault_path, mapping)
    return True


def apply_map(mapping: Dict[str, str], env: Dict[str, str]) -> Dict[str, str]:
    """Return a new dict with keys renamed according to *mapping*.

    Keys not present in *mapping* are passed through unchanged.
    """
    result: Dict[str, str] = {}
    for k, v in env.items():
        result[mapping.get(k, k)] = v
    return result
