"""Vault file read/write operations for envault."""

import json
from pathlib import Path
from typing import Dict

from envault.crypto import encrypt, decrypt

VAULT_FILENAME = ".env.vault"


def load_vault(vault_path: Path, passphrase: str) -> Dict[str, str]:
    """Load and decrypt all key-value pairs from a vault file."""
    if not vault_path.exists():
        return {}

    raw = vault_path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}

    decrypted = decrypt(raw, passphrase)
    return json.loads(decrypted)


def save_vault(vault_path: Path, passphrase: str, data: Dict[str, str]) -> None:
    """Encrypt and save key-value pairs to a vault file."""
    plaintext = json.dumps(data, sort_keys=True, indent=2)
    encoded = encrypt(plaintext, passphrase)
    vault_path.write_text(encoded + "\n", encoding="utf-8")


def get_default_vault_path(project_dir: Path | None = None) -> Path:
    """Return the default vault file path for a project directory."""
    base = project_dir or Path.cwd()
    return base / VAULT_FILENAME
