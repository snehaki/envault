"""Secure vault sharing: export an encrypted bundle and import it."""

from __future__ import annotations

import base64
import json
import os
from typing import Dict

from envault.crypto import decrypt, encrypt


def export_bundle(
    vault: Dict[str, str],
    src_passphrase: str,
    bundle_passphrase: str,
) -> str:
    """Decrypt every value in *vault* and re-encrypt with *bundle_passphrase*.

    Returns a base64-encoded JSON string that can be shared safely.
    """
    bundle: Dict[str, str] = {}
    for key, ciphertext in vault.items():
        plaintext = decrypt(ciphertext, src_passphrase)
        bundle[key] = encrypt(plaintext, bundle_passphrase)

    payload = json.dumps(bundle, sort_keys=True)
    return base64.b64encode(payload.encode()).decode()


def import_bundle(
    bundle_b64: str,
    bundle_passphrase: str,
    dest_passphrase: str,
) -> Dict[str, str]:
    """Decode *bundle_b64*, decrypt with *bundle_passphrase*, re-encrypt with
    *dest_passphrase*, and return the resulting vault dict.
    """
    payload = base64.b64decode(bundle_b64.encode()).decode()
    bundle: Dict[str, str] = json.loads(payload)

    vault: Dict[str, str] = {}
    for key, ciphertext in bundle.items():
        plaintext = decrypt(ciphertext, bundle_passphrase)
        vault[key] = encrypt(plaintext, dest_passphrase)

    return vault


def write_bundle_file(bundle_b64: str, path: str) -> None:
    """Write a bundle string to *path*."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(bundle_b64 + "\n")


def read_bundle_file(path: str) -> str:
    """Read a bundle string from *path*."""
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read().strip()
