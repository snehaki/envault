"""Per-key value history tracking for envault."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MAX_HISTORY = 20


def _history_path(vault_path: Path) -> Path:
    return vault_path.parent / (vault_path.stem + ".history.json")


def load_history(vault_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Return the full history mapping {key: [{ciphertext, timestamp}, ...]}"""
    path = _history_path(vault_path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_history(vault_path: Path, history: dict[str, list[dict[str, Any]]]) -> None:
    path = _history_path(vault_path)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(history, fh, indent=2)


def record_value(
    vault_path: Path,
    key: str,
    ciphertext: str,
    timestamp: str,
) -> None:
    """Append *ciphertext* to the history for *key*, capping at MAX_HISTORY entries."""
    history = load_history(vault_path)
    entries = history.setdefault(key, [])
    entries.append({"ciphertext": ciphertext, "timestamp": timestamp})
    if len(entries) > MAX_HISTORY:
        entries[:] = entries[-MAX_HISTORY:]
    save_history(vault_path, history)


def get_history(vault_path: Path, key: str) -> list[dict[str, Any]]:
    """Return history entries for *key*, oldest first."""
    return load_history(vault_path).get(key, [])


def clear_history(vault_path: Path, key: str) -> None:
    """Remove all history entries for *key*."""
    history = load_history(vault_path)
    history.pop(key, None)
    save_history(vault_path, history)
