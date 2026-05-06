"""Compare a live environment against vault secrets."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.crypto import decrypt
from envault.vault import load_vault


@dataclass
class EnvDiffResult:
    missing: List[str] = field(default_factory=list)   # in vault, not in env
    extra: List[str] = field(default_factory=list)     # in env, not in vault
    mismatched: List[str] = field(default_factory=list)  # value differs
    matched: List[str] = field(default_factory=list)   # identical

    @property
    def ok(self) -> bool:
        return not (self.missing or self.extra or self.mismatched)

    def summary(self) -> str:
        lines = []
        for k in sorted(self.missing):
            lines.append(f"  MISSING   {k}")
        for k in sorted(self.extra):
            lines.append(f"  EXTRA     {k}")
        for k in sorted(self.mismatched):
            lines.append(f"  MISMATCH  {k}")
        for k in sorted(self.matched):
            lines.append(f"  OK        {k}")
        return "\n".join(lines) if lines else "  (no keys)"


def compare_env_to_vault(
    vault_path: str,
    passphrase: str,
    env: Optional[Dict[str, str]] = None,
    *,
    include_extra: bool = True,
) -> EnvDiffResult:
    """Decrypt all vault secrets and compare values against *env* (default: os.environ)."""
    if env is None:
        env = dict(os.environ)

    vault = load_vault(vault_path)
    secrets: Dict[str, str] = vault.get("secrets", {})

    result = EnvDiffResult()

    for key, ciphertext in secrets.items():
        if key not in env:
            result.missing.append(key)
            continue
        try:
            plaintext = decrypt(ciphertext, passphrase)
        except Exception:
            # Can't decrypt — treat as mismatch rather than crashing
            result.mismatched.append(key)
            continue
        if env[key] == plaintext:
            result.matched.append(key)
        else:
            result.mismatched.append(key)

    if include_extra:
        vault_keys = set(secrets.keys())
        for key in env:
            if key not in vault_keys:
                result.extra.append(key)

    return result
