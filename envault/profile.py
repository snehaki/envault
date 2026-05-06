"""Profile support: named sets of vault overrides for different environments (dev, staging, prod)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

PROFILES_FILENAME = ".envault-profiles.json"


def _profiles_path(vault_path: str) -> Path:
    return Path(vault_path).parent / PROFILES_FILENAME


def load_profiles(vault_path: str) -> Dict[str, List[str]]:
    """Return mapping of profile_name -> list of keys included in that profile."""
    path = _profiles_path(vault_path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        return {}
    return {k: list(v) for k, v in data.items() if isinstance(v, list)}


def save_profiles(vault_path: str, profiles: Dict[str, List[str]]) -> None:
    """Persist profiles mapping to disk."""
    path = _profiles_path(vault_path)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(profiles, fh, indent=2, sort_keys=True)


def create_profile(vault_path: str, name: str, keys: List[str]) -> None:
    """Create or overwrite a named profile with the given keys."""
    if not name:
        raise ValueError("Profile name must not be empty.")
    profiles = load_profiles(vault_path)
    profiles[name] = sorted(set(keys))
    save_profiles(vault_path, profiles)


def delete_profile(vault_path: str, name: str) -> None:
    """Remove a profile by name; raises KeyError if not found."""
    profiles = load_profiles(vault_path)
    if name not in profiles:
        raise KeyError(f"Profile '{name}' does not exist.")
    del profiles[name]
    save_profiles(vault_path, profiles)


def get_profile_keys(vault_path: str, name: str) -> List[str]:
    """Return the list of keys for a profile; raises KeyError if not found."""
    profiles = load_profiles(vault_path)
    if name not in profiles:
        raise KeyError(f"Profile '{name}' does not exist.")
    return profiles[name]


def list_profiles(vault_path: str) -> List[str]:
    """Return sorted list of profile names."""
    return sorted(load_profiles(vault_path).keys())


def profile_keys_from_vault(
    vault_path: str, profile_name: str, vault_data: dict
) -> Dict[str, Optional[str]]:
    """Return {key: encrypted_value_or_None} for every key in the profile."""
    keys = get_profile_keys(vault_path, profile_name)
    secrets = vault_data.get("secrets", {})
    return {k: secrets.get(k) for k in keys}
