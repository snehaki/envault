"""Key dependency tracking — define which keys depend on others."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def _deps_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".dependencies.json")


def load_dependencies(vault_path: str) -> Dict[str, List[str]]:
    """Return mapping of key -> list of keys it depends on."""
    p = _deps_path(vault_path)
    if not p.exists():
        return {}
    data = json.loads(p.read_text())
    if not isinstance(data, dict):
        return {}
    return {k: list(v) for k, v in data.items() if isinstance(v, list)}


def save_dependencies(vault_path: str, deps: Dict[str, List[str]]) -> None:
    p = _deps_path(vault_path)
    p.write_text(json.dumps(deps, indent=2, sort_keys=True))


def set_dependency(vault_path: str, key: str, depends_on: List[str]) -> None:
    """Record that *key* depends on every key in *depends_on*."""
    if not key:
        raise ValueError("key must not be empty")
    if not depends_on:
        raise ValueError("depends_on must not be empty")
    if key in depends_on:
        raise ValueError(f"key '{key}' cannot depend on itself")
    deps = load_dependencies(vault_path)
    deps[key] = sorted(set(depends_on))
    save_dependencies(vault_path, deps)


def remove_dependency(vault_path: str, key: str) -> bool:
    """Remove dependency entry for *key*. Returns True if it existed."""
    deps = load_dependencies(vault_path)
    if key not in deps:
        return False
    del deps[key]
    save_dependencies(vault_path, deps)
    return True


def get_dependents(vault_path: str, key: str) -> List[str]:
    """Return keys that list *key* as a dependency (reverse lookup)."""
    deps = load_dependencies(vault_path)
    return sorted(k for k, v in deps.items() if key in v)


def resolve_order(vault_path: str, keys: List[str]) -> List[str]:
    """Return *keys* in topological order (dependencies first).

    Raises ValueError on cycles.
    """
    deps = load_dependencies(vault_path)
    visited: set = set()
    result: List[str] = []
    in_stack: set = set()

    def visit(k: str) -> None:
        if k in in_stack:
            raise ValueError(f"Circular dependency detected involving '{k}'")
        if k in visited:
            return
        in_stack.add(k)
        for dep in deps.get(k, []):
            visit(dep)
        in_stack.discard(k)
        visited.add(k)
        result.append(k)

    for key in keys:
        visit(key)
    return result
