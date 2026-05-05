"""Key rotation: re-encrypt all vault secrets under a new passphrase."""

from __future__ import annotations

from typing import TYPE_CHECKING

from envault.crypto import decrypt, encrypt
from envault.vault import load_vault, save_vault

if TYPE_CHECKING:
    from pathlib import Path


def rotate_key(
    vault_path: "Path",
    old_passphrase: str,
    new_passphrase: str,
) -> list[str]:
    """Re-encrypt every secret in *vault_path* with *new_passphrase*.

    Returns a list of key names that were rotated.

    Raises
    ------
    ValueError
        If *old_passphrase* cannot decrypt one or more entries (rotation is
        aborted before any writes so the vault is left untouched).
    FileNotFoundError
        If *vault_path* does not exist.
    """
    vault = load_vault(vault_path)
    secrets: dict = vault.get("secrets", {})

    if not secrets:
        return []

    # --- Decrypt everything first so we fail fast before touching the file ---
    plaintext_map: dict[str, str] = {}
    for key, ciphertext in secrets.items():
        try:
            plaintext_map[key] = decrypt(ciphertext, old_passphrase)
        except Exception as exc:
            raise ValueError(
                f"Failed to decrypt '{key}' with the supplied old passphrase: {exc}"
            ) from exc

    # --- Re-encrypt under the new passphrase ---
    new_secrets: dict[str, str] = {
        key: encrypt(plaintext, new_passphrase)
        for key, plaintext in plaintext_map.items()
    }

    vault["secrets"] = new_secrets
    save_vault(vault_path, vault)

    return list(new_secrets.keys())
