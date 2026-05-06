"""Check vault keys against a reference .env.example file."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CheckResult:
    missing_in_vault: list[str] = field(default_factory=list)   # in example, not in vault
    extra_in_vault: list[str] = field(default_factory=list)     # in vault, not in example

    @property
    def ok(self) -> bool:
        return not self.missing_in_vault and not self.extra_in_vault

    def summary(self) -> str:
        lines = []
        for k in sorted(self.missing_in_vault):
            lines.append(f"  MISSING  {k}")
        for k in sorted(self.extra_in_vault):
            lines.append(f"  EXTRA    {k}")
        if not lines:
            return "vault matches .env.example"
        return "\n".join(lines)


_KEY_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=')


def parse_example_keys(path: Path) -> set[str]:
    """Return all key names defined in a .env.example file."""
    keys: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _KEY_RE.match(line)
        if m:
            keys.add(m.group(1))
    return keys


def check_vault(
    vault: dict,
    example_path: Path,
    *,
    ignore_extra: bool = False,
) -> CheckResult:
    """Compare vault keys with those declared in *example_path*.

    Args:
        vault: loaded vault dict (keys are env-var names, values are encrypted blobs).
        example_path: path to .env.example.
        ignore_extra: when True, keys present in the vault but absent from the
            example are not reported.

    Returns:
        A :class:`CheckResult` describing any discrepancies.
    """
    example_keys = parse_example_keys(example_path)
    vault_keys = set(vault.get("keys", {}).keys())

    result = CheckResult()
    result.missing_in_vault = sorted(example_keys - vault_keys)
    if not ignore_extra:
        result.extra_in_vault = sorted(vault_keys - example_keys)
    return result
