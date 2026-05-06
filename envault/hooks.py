"""Pre/post hook support for envault CLI commands.

Hooks are shell commands stored in the vault metadata and executed
before or after specific envault operations (set, get, delete, export).
"""

from __future__ import annotations

import subprocess
import json
from pathlib import Path
from typing import Optional

HOOKS_FILENAME = ".envault-hooks.json"

VALID_EVENTS = frozenset(["pre-set", "post-set", "pre-get", "post-get",
                           "pre-delete", "post-delete", "pre-export", "post-export"])


def _hooks_path(vault_path: Path) -> Path:
    return vault_path.parent / HOOKS_FILENAME


def load_hooks(vault_path: Path) -> dict[str, list[str]]:
    """Load hooks config from the hooks file next to the vault."""
    path = _hooks_path(vault_path)
    if not path.exists():
        return {}
    with path.open("r") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if k in VALID_EVENTS}


def save_hooks(vault_path: Path, hooks: dict[str, list[str]]) -> None:
    """Persist hooks config to disk."""
    path = _hooks_path(vault_path)
    with path.open("w") as f:
        json.dump(hooks, f, indent=2)


def add_hook(vault_path: Path, event: str, command: str) -> None:
    """Register a shell command to run on *event*."""
    if event not in VALID_EVENTS:
        raise ValueError(f"Unknown event '{event}'. Valid events: {sorted(VALID_EVENTS)}")
    hooks = load_hooks(vault_path)
    hooks.setdefault(event, [])
    if command not in hooks[event]:
        hooks[event].append(command)
    save_hooks(vault_path, hooks)


def remove_hook(vault_path: Path, event: str, command: str) -> bool:
    """Remove a specific command from an event. Returns True if removed."""
    hooks = load_hooks(vault_path)
    cmds = hooks.get(event, [])
    if command not in cmds:
        return False
    cmds.remove(command)
    if not cmds:
        del hooks[event]
    save_hooks(vault_path, hooks)
    return True


def run_hooks(vault_path: Path, event: str, env: Optional[dict] = None) -> list[tuple[str, int]]:
    """Execute all hooks for *event*. Returns list of (command, returncode)."""
    hooks = load_hooks(vault_path)
    results = []
    for cmd in hooks.get(event, []):
        result = subprocess.run(cmd, shell=True, env=env)
        results.append((cmd, result.returncode))
    return results
