"""Git-friendly diff utilities for vault snapshots."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class VaultDiff:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines = []
        for key in sorted(self.added):
            lines.append(f"  + {key}")
        for key in sorted(self.removed):
            lines.append(f"  - {key}")
        for key in sorted(self.changed):
            lines.append(f"  ~ {key}")
        return "\n".join(lines) if lines else "  (no changes)"


def diff_vaults(
    old: Dict[str, str],
    new: Dict[str, str],
) -> VaultDiff:
    """Compare two vault dicts (key -> encrypted_value) by key presence.

    Values are encrypted, so we compare ciphertext blobs to detect changes.
    A changed entry means the ciphertext differs (i.e. the plaintext was updated).
    """
    old_keys = set(old)
    new_keys = set(new)

    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)
    changed = sorted(
        k for k in old_keys & new_keys if old[k] != new[k]
    )
    return VaultDiff(added=added, removed=removed, changed=changed)


def snapshot_keys(vault: Dict[str, str]) -> str:
    """Return a stable, git-diffable text representation of vault keys.

    Only key names (not secret values) are included so the snapshot is
    safe to commit alongside the encrypted vault file.
    """
    keys = sorted(vault.keys())
    return json.dumps(keys, indent=2)
