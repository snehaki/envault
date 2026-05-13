"""Scope support: restrict vault keys to named environments (e.g. dev, staging, prod)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

_VALID_SCOPES = {"dev", "staging", "prod", "test", "local"}


def _scopes_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".scopes.json")


def load_scopes(vault_path: str) -> Dict[str, List[str]]:
    """Return mapping of key -> list[scope]."""
    p = _scopes_path(vault_path)
    if not p.exists():
        return {}
    data = json.loads(p.read_text())
    if not isinstance(data, dict):
        return {}
    return {k: list(v) for k, v in data.items() if isinstance(v, list)}


def save_scopes(vault_path: str, scopes: Dict[str, List[str]]) -> None:
    p = _scopes_path(vault_path)
    p.write_text(json.dumps(scopes, indent=2, sort_keys=True))


def set_scope(vault_path: str, key: str, scope_list: List[str]) -> None:
    """Assign one or more scopes to a key. Raises ValueError for unknown scopes."""
    if not key:
        raise ValueError("key must not be empty")
    unknown = set(scope_list) - _VALID_SCOPES
    if unknown:
        raise ValueError(f"Unknown scopes: {sorted(unknown)}. Valid: {sorted(_VALID_SCOPES)}")
    scopes = load_scopes(vault_path)
    scopes[key] = sorted(set(scope_list))
    save_scopes(vault_path, scopes)


def remove_scope(vault_path: str, key: str) -> bool:
    """Remove scope entry for key. Returns True if an entry was removed."""
    scopes = load_scopes(vault_path)
    if key not in scopes:
        return False
    del scopes[key]
    save_scopes(vault_path, scopes)
    return True


def get_scopes(vault_path: str, key: str) -> List[str]:
    """Return scopes assigned to key, or empty list."""
    return load_scopes(vault_path).get(key, [])


def keys_in_scope(vault_path: str, scope: str) -> List[str]:
    """Return sorted list of keys that include the given scope."""
    scopes = load_scopes(vault_path)
    return sorted(k for k, v in scopes.items() if scope in v)


def valid_scopes() -> List[str]:
    return sorted(_VALID_SCOPES)
