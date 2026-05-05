"""Export and import functionality for envault vaults."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from envault.crypto import decrypt, encrypt
from envault.vault import load_vault, save_vault


def export_env(vault_path: Path, passphrase: str, output_path: Optional[Path] = None) -> str:
    """Decrypt all secrets and export them as a .env file.

    Returns the content as a string. Optionally writes to output_path.
    """
    vault = load_vault(vault_path)
    lines: list[str] = []

    for key in sorted(vault.keys()):
        raw_value = decrypt(vault[key], passphrase)
        # Wrap value in quotes if it contains spaces or special chars
        if any(c in raw_value for c in (" ", "#", "'", '"')):
            raw_value = '"' + raw_value.replace('"', '\\"') + '"'
        lines.append(f"{key}={raw_value}")

    content = "\n".join(lines) + ("\n" if lines else "")

    if output_path is not None:
        output_path.write_text(content, encoding="utf-8")

    return content


def import_env(vault_path: Path, passphrase: str, env_path: Path, overwrite: bool = False) -> list[str]:
    """Read a .env file and encrypt each variable into the vault.

    Returns a list of keys that were imported.
    Skips blank lines and comments.
    Raises ValueError if a key already exists and overwrite is False.
    """
    vault = load_vault(vault_path)
    imported: list[str] = []

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        # Strip surrounding quotes from value
        value = value.strip().strip('"').strip("'")

        if key in vault and not overwrite:
            raise ValueError(f"Key '{key}' already exists. Use --overwrite to replace it.")

        vault[key] = encrypt(value, passphrase)
        imported.append(key)

    save_vault(vault_path, vault)
    return imported
