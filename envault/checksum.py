"""Per-key checksum tracking for vault integrity verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Optional


def _checksum_path(vault_path: str) -> Path:
    p = Path(vault_path)
    return p.with_suffix(".checksums.json")


def load_checksums(vault_path: str) -> Dict[str, str]:
    """Load the checksum sidecar file, returning an empty dict if absent."""
    path = _checksum_path(vault_path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, str)}


def save_checksums(vault_path: str, checksums: Dict[str, str]) -> None:
    """Persist the checksum mapping to disk."""
    path = _checksum_path(vault_path)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(checksums, fh, indent=2, sort_keys=True)


def _hash(ciphertext: str) -> str:
    """Return a stable SHA-256 hex digest of a ciphertext string."""
    return hashlib.sha256(ciphertext.encode("utf-8")).hexdigest()


def record_checksum(vault_path: str, key: str, ciphertext: str) -> str:
    """Store (or update) the checksum for *key* and return the digest."""
    checksums = load_checksums(vault_path)
    digest = _hash(ciphertext)
    checksums[key] = digest
    save_checksums(vault_path, checksums)
    return digest


def remove_checksum(vault_path: str, key: str) -> bool:
    """Remove the checksum entry for *key*. Returns True if it existed."""
    checksums = load_checksums(vault_path)
    if key not in checksums:
        return False
    del checksums[key]
    save_checksums(vault_path, checksums)
    return True


def verify_checksum(vault_path: str, key: str, ciphertext: str) -> bool:
    """Return True when the stored digest matches the given ciphertext."""
    checksums = load_checksums(vault_path)
    if key not in checksums:
        return False
    return checksums[key] == _hash(ciphertext)


def verify_all(vault_path: str, vault_data: Dict[str, str]) -> Dict[str, bool]:
    """Verify every key in *vault_data* against stored checksums.

    Returns a mapping of key -> bool (True = intact, False = tampered/missing).
    Keys present in the vault but absent from the checksum file are marked False.
    """
    checksums = load_checksums(vault_path)
    results: Dict[str, bool] = {}
    for key, ciphertext in vault_data.items():
        if key not in checksums:
            results[key] = False
        else:
            results[key] = checksums[key] == _hash(ciphertext)
    return results
