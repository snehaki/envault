"""Search and filter vault keys by pattern or value presence."""

from __future__ import annotations

import fnmatch
import re
from typing import Optional

from envault.crypto import decrypt
from envault.vault import load_vault


def search_keys(
    vault: dict,
    passphrase: str,
    pattern: str,
    *,
    search_values: bool = False,
    regex: bool = False,
) -> list[dict]:
    """Return matching entries from the vault.

    Args:
        vault: Loaded vault dict (from load_vault).
        passphrase: Passphrase to decrypt values when search_values is True.
        pattern: Glob pattern (default) or regex string.
        search_values: If True, also decrypt and search inside values.
        regex: If True, treat pattern as a regular expression.

    Returns:
        List of dicts with 'key' and optionally 'value' fields.
    """
    entries = vault.get("entries", {})
    results: list[dict] = []

    compiled: Optional[re.Pattern] = None
    if regex:
        compiled = re.compile(pattern, re.IGNORECASE)

    def _matches_str(text: str) -> bool:
        if compiled is not None:
            return bool(compiled.search(text))
        return fnmatch.fnmatchcase(text.lower(), pattern.lower())

    for key, ciphertext in entries.items():
        key_match = _matches_str(key)
        value_match = False

        if search_values:
            try:
                plaintext = decrypt(ciphertext, passphrase)
                value_match = _matches_str(plaintext)
            except Exception:
                pass

        if key_match or value_match:
            record: dict = {"key": key}
            if search_values:
                try:
                    record["value"] = decrypt(ciphertext, passphrase)
                except Exception:
                    record["value"] = "<decryption error>"
            results.append(record)

    results.sort(key=lambda r: r["key"])
    return results


def filter_by_prefix(vault: dict, prefix: str) -> list[str]:
    """Return sorted list of keys that start with the given prefix."""
    entries = vault.get("entries", {})
    return sorted(k for k in entries if k.startswith(prefix))
