"""Sync vault keys from a remote source (e.g. another vault file or URL).

Supports merging keys from a source vault into the current vault,
with configurable conflict resolution strategies.
"""

from __future__ import annotations

from enum import Enum
from typing import NamedTuple

from envault.crypto import decrypt, encrypt
from envault.vault import load_vault, save_vault


class ConflictStrategy(str, Enum):
    KEEP_LOCAL = "keep_local"   # local value wins on conflict
    TAKE_REMOTE = "take_remote" # remote value wins on conflict
    SKIP = "skip"               # skip conflicting keys entirely


class SyncResult(NamedTuple):
    added: list[str]
    updated: list[str]
    skipped: list[str]

    @property
    def ok(self) -> bool:
        return True

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.updated:
            parts.append(f"{len(self.updated)} updated")
        if self.skipped:
            parts.append(f"{len(self.skipped)} skipped")
        return ", ".join(parts) if parts else "no changes"


def sync_vaults(
    local_path: str,
    remote_path: str,
    local_passphrase: str,
    remote_passphrase: str,
    strategy: ConflictStrategy = ConflictStrategy.KEEP_LOCAL,
    keys: list[str] | None = None,
) -> SyncResult:
    """Merge keys from remote vault into local vault.

    Args:
        local_path: Path to the destination vault.
        remote_path: Path to the source vault.
        local_passphrase: Passphrase for the local vault.
        remote_passphrase: Passphrase for the remote vault.
        strategy: How to handle keys that exist in both vaults.
        keys: Optional list of specific keys to sync; None means all.

    Returns:
        SyncResult describing what changed.
    """
    local_vault = load_vault(local_path)
    remote_vault = load_vault(remote_path)

    local_secrets: dict[str, str] = local_vault.get("secrets", {})
    remote_secrets: dict[str, str] = remote_vault.get("secrets", {})

    candidates = keys if keys is not None else list(remote_secrets.keys())

    added: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []

    for key in candidates:
        if key not in remote_secrets:
            skipped.append(key)
            continue

        plaintext = decrypt(remote_secrets[key], remote_passphrase)
        new_ciphertext = encrypt(plaintext, local_passphrase)

        if key not in local_secrets:
            local_secrets[key] = new_ciphertext
            added.append(key)
        else:
            if strategy == ConflictStrategy.KEEP_LOCAL:
                skipped.append(key)
            elif strategy == ConflictStrategy.TAKE_REMOTE:
                local_secrets[key] = new_ciphertext
                updated.append(key)
            else:  # SKIP
                skipped.append(key)

    local_vault["secrets"] = local_secrets
    save_vault(local_path, local_vault)

    return SyncResult(added=added, updated=updated, skipped=skipped)
