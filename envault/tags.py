"""Tag management for vault keys — assign, remove, and filter keys by tag."""

from __future__ import annotations

from typing import Dict, List, Optional

TAGS_META_KEY = "__tags__"


def get_tags(vault: dict, key: str) -> List[str]:
    """Return the list of tags assigned to a vault key."""
    meta: Dict[str, List[str]] = vault.get(TAGS_META_KEY, {})
    return list(meta.get(key, []))


def set_tags(vault: dict, key: str, tags: List[str]) -> dict:
    """Assign a list of tags to a vault key, replacing any existing tags."""
    if TAGS_META_KEY not in vault:
        vault[TAGS_META_KEY] = {}
    if tags:
        vault[TAGS_META_KEY][key] = sorted(set(tags))
    else:
        vault[TAGS_META_KEY].pop(key, None)
    return vault


def add_tag(vault: dict, key: str, tag: str) -> dict:
    """Add a single tag to a vault key without removing existing tags."""
    current = get_tags(vault, key)
    if tag not in current:
        current.append(tag)
    return set_tags(vault, key, current)


def remove_tag(vault: dict, key: str, tag: str) -> dict:
    """Remove a single tag from a vault key. No-op if the tag is absent."""
    current = get_tags(vault, key)
    current = [t for t in current if t != tag]
    return set_tags(vault, key, current)


def keys_by_tag(vault: dict, tag: str) -> List[str]:
    """Return all vault keys that carry the given tag, sorted alphabetically."""
    meta: Dict[str, List[str]] = vault.get(TAGS_META_KEY, {})
    return sorted(k for k, tags in meta.items() if tag in tags)


def all_tags(vault: dict) -> List[str]:
    """Return a deduplicated, sorted list of every tag used in the vault."""
    meta: Dict[str, List[str]] = vault.get(TAGS_META_KEY, {})
    seen: set = set()
    for tags in meta.values():
        seen.update(tags)
    return sorted(seen)


def purge_key(vault: dict, key: str) -> dict:
    """Remove all tag metadata for a given key (call when a key is deleted)."""
    if TAGS_META_KEY in vault:
        vault[TAGS_META_KEY].pop(key, None)
    return vault
