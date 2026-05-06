"""Backup and restore vault snapshots to/from a single archive file."""

from __future__ import annotations

import json
import base64
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from envault.vault import load_vault, save_vault


BACKUP_VERSION = 1


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _checksum(data: dict) -> str:
    """Return a short SHA-256 hex digest of the JSON-serialised data."""
    raw = json.dumps(data, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def create_backup(vault_path: Path) -> dict:
    """Serialise a vault file into a portable backup dict.

    The backup is self-contained: it embeds the raw vault contents
    (already encrypted) plus metadata so it can be restored later.
    """
    vault = load_vault(vault_path)
    payload = {
        "version": BACKUP_VERSION,
        "created_at": _now_utc(),
        "source": str(vault_path),
        "vault": vault,
    }
    payload["checksum"] = _checksum(vault)
    return payload


def write_backup_file(vault_path: Path, dest: Path) -> Path:
    """Write a backup of *vault_path* to *dest* and return the path."""
    payload = create_backup(vault_path)
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    dest.write_text(encoded)
    return dest


def read_backup_file(backup_path: Path) -> dict:
    """Read and decode a backup file, raising ValueError on corruption."""
    try:
        raw = base64.b64decode(backup_path.read_text())
        payload = json.loads(raw)
    except Exception as exc:
        raise ValueError(f"Cannot read backup file: {exc}") from exc

    if payload.get("version") != BACKUP_VERSION:
        raise ValueError("Unsupported backup version.")

    stored_checksum = payload.pop("checksum", None)
    if stored_checksum != _checksum(payload["vault"]):
        raise ValueError("Backup checksum mismatch — file may be corrupted.")

    payload["checksum"] = stored_checksum  # restore for callers
    return payload


def restore_backup(backup_path: Path, dest_vault: Optional[Path] = None) -> Path:
    """Restore a vault from *backup_path*.

    If *dest_vault* is None the original source path embedded in the
    backup is used.  Returns the path that was written.
    """
    payload = read_backup_file(backup_path)
    target = dest_vault or Path(payload["source"])
    save_vault(target, payload["vault"])
    return target
