"""cascade.py — propagate a key's value to dependent keys in the vault."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from envault.crypto import decrypt, encrypt
from envault.dependency import load_dependencies
from envault.vault import load_vault, save_vault


@dataclass
class CascadeResult:
    source_key: str
    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.skipped) == 0

    def summary(self) -> str:
        parts = []
        if self.updated:
            parts.append(f"updated {len(self.updated)} dependent key(s): {', '.join(self.updated)}")
        if self.skipped:
            parts.append(f"skipped {len(self.skipped)} key(s): {', '.join(self.skipped)}")
        if not parts:
            return f"no dependents found for '{self.source_key}'"
        return "; ".join(parts)


def cascade_value(
    vault_path: Path,
    source_key: str,
    old_passphrase: str,
    new_passphrase: Optional[str] = None,
) -> CascadeResult:
    """Re-encrypt all keys that depend on *source_key* using the source key's
    current plaintext value.  If *new_passphrase* is omitted the vault
    passphrase is assumed to be the same for all keys."""
    if new_passphrase is None:
        new_passphrase = old_passphrase

    vault = load_vault(vault_path)
    deps = load_dependencies(vault_path)
    result = CascadeResult(source_key=source_key)

    if source_key not in vault:
        raise KeyError(f"source key '{source_key}' not found in vault")

    source_plain = decrypt(vault[source_key], old_passphrase)

    dependents: list[str] = deps.get(source_key, {}).get("dependents", [])

    for dep_key in dependents:
        if dep_key not in vault:
            result.skipped.append(dep_key)
            continue
        vault[dep_key] = encrypt(source_plain, new_passphrase)
        result.updated.append(dep_key)

    if result.updated:
        save_vault(vault_path, vault)

    return result
