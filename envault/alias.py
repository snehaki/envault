"""Key alias support: define short aliases that map to full vault keys."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


def _aliases_path(vault_path: str) -> Path:
    p = Path(vault_path)
    return p.with_suffix(".aliases.json")


def load_aliases(vault_path: str) -> Dict[str, str]:
    """Return mapping of alias -> key. Empty dict if no file exists."""
    path = _aliases_path(vault_path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def save_aliases(vault_path: str, aliases: Dict[str, str]) -> None:
    """Persist the alias mapping to the sidecar file."""
    path = _aliases_path(vault_path)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(aliases, fh, indent=2, sort_keys=True)


def set_alias(vault_path: str, alias: str, key: str) -> None:
    """Create or overwrite *alias* pointing to *key*."""
    if not alias:
        raise ValueError("Alias name must not be empty.")
    if not key:
        raise ValueError("Target key must not be empty.")
    aliases = load_aliases(vault_path)
    aliases[alias] = key
    save_aliases(vault_path, aliases)


def remove_alias(vault_path: str, alias: str) -> bool:
    """Remove *alias*. Returns True if it existed, False otherwise."""
    aliases = load_aliases(vault_path)
    if alias not in aliases:
        return False
    del aliases[alias]
    save_aliases(vault_path, aliases)
    return True


def resolve_alias(vault_path: str, name: str) -> Optional[str]:
    """Return the key that *name* is an alias for, or None."""
    return load_aliases(vault_path).get(name)


def list_aliases(vault_path: str) -> Dict[str, str]:
    """Return all aliases sorted by alias name."""
    return dict(sorted(load_aliases(vault_path).items()))
