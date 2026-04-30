"""Encryption and decryption utilities for envault using AES-GCM."""

import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


NONCE_SIZE = 12  # bytes, standard for AES-GCM
KEY_SIZE = 32    # bytes, AES-256


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a passphrase using PBKDF2-HMAC-SHA256."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        passphrase.encode("utf-8"),
        salt,
        iterations=260_000,
        dklen=KEY_SIZE,
    )


def encrypt(plaintext: str, passphrase: str) -> str:
    """Encrypt plaintext and return a base64-encoded ciphertext string.

    Format: base64(salt + nonce + ciphertext)
    """
    salt = os.urandom(16)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    payload = salt + nonce + ciphertext
    return base64.b64encode(payload).decode("ascii")


def decrypt(encoded: str, passphrase: str) -> str:
    """Decrypt a base64-encoded ciphertext string and return plaintext."""
    payload = base64.b64decode(encoded.encode("ascii"))
    salt = payload[:16]
    nonce = payload[16:16 + NONCE_SIZE]
    ciphertext = payload[16 + NONCE_SIZE:]
    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")
