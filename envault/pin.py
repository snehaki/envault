"""Per-key PIN protection: require a secondary PIN to read sensitive keys."""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
from typing import Optional


def _pins_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".pins.json")


def load_pins(vault_path: str) -> dict:
    p = _pins_path(vault_path)
    if not p.exists():
        return {}
    with open(p) as f:
        return json.load(f)


def save_pins(vault_path: str, pins: dict) -> None:
    p = _pins_path(vault_path)
    with open(p, "w") as f:
        json.dump(pins, f, indent=2)


def _hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


def set_pin(vault_path: str, key: str, pin: str) -> None:
    """Protect *key* with a PIN (stored as SHA-256 hash)."""
    if not pin:
        raise ValueError("PIN must not be empty.")
    if len(pin) < 4:
        raise ValueError("PIN must be at least 4 characters.")
    pins = load_pins(vault_path)
    pins[key] = _hash_pin(pin)
    save_pins(vault_path, pins)


def remove_pin(vault_path: str, key: str) -> bool:
    """Remove PIN protection from *key*. Returns True if a PIN existed."""
    pins = load_pins(vault_path)
    if key in pins:
        del pins[key]
        save_pins(vault_path, pins)
        return True
    return False


def verify_pin(vault_path: str, key: str, pin: str) -> bool:
    """Return True when *pin* matches the stored hash for *key*."""
    pins = load_pins(vault_path)
    if key not in pins:
        return True  # no PIN set — access allowed
    return pins[key] == _hash_pin(pin)


def is_pinned(vault_path: str, key: str) -> bool:
    """Return True if *key* has a PIN set."""
    return key in load_pins(vault_path)


def pinned_keys(vault_path: str) -> list[str]:
    """Return sorted list of keys that have a PIN set."""
    return sorted(load_pins(vault_path).keys())
