"""Namespace support: group vault keys under logical prefixes (e.g. APP__, DB__)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

_NAMESPACE_SUFFIX = ".namespaces.json"


def _namespaces_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix("") .parent / (Path(vault_path).name + _NAMESPACE_SUFFIX)


def load_namespaces(vault_path: str) -> Dict[str, str]:
    """Return mapping of key -> namespace label."""
    p = _namespaces_path(vault_path)
    if not p.exists():
        return {}
    with p.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, str)}


def save_namespaces(vault_path: str, mapping: Dict[str, str]) -> None:
    p = _namespaces_path(vault_path)
    with p.open("w") as f:
        json.dump(mapping, f, indent=2)


def set_namespace(vault_path: str, key: str, namespace: str) -> None:
    """Assign *key* to *namespace*."""
    if not key:
        raise ValueError("key must not be empty")
    if not namespace:
        raise ValueError("namespace must not be empty")
    mapping = load_namespaces(vault_path)
    mapping[key] = namespace
    save_namespaces(vault_path, mapping)


def remove_namespace(vault_path: str, key: str) -> bool:
    """Remove namespace assignment for *key*. Returns True if it existed."""
    mapping = load_namespaces(vault_path)
    if key not in mapping:
        return False
    del mapping[key]
    save_namespaces(vault_path, mapping)
    return True


def keys_in_namespace(vault_path: str, namespace: str) -> List[str]:
    """Return sorted list of keys that belong to *namespace*."""
    mapping = load_namespaces(vault_path)
    return sorted(k for k, ns in mapping.items() if ns == namespace)


def list_namespaces(vault_path: str) -> List[str]:
    """Return sorted unique list of namespace labels in use."""
    mapping = load_namespaces(vault_path)
    return sorted(set(mapping.values()))
