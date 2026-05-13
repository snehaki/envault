"""Key rating/priority system: assign a numeric priority (1-5) to vault keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

MIN_RATING = 1
MAX_RATING = 5


def _ratings_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".ratings.json")


def load_ratings(vault_path: str) -> Dict[str, int]:
    """Return {key: rating} mapping; empty dict if sidecar absent."""
    p = _ratings_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def save_ratings(vault_path: str, ratings: Dict[str, int]) -> None:
    p = _ratings_path(vault_path)
    p.write_text(json.dumps(ratings, indent=2, sort_keys=True))


def set_rating(vault_path: str, key: str, rating: int) -> None:
    """Assign a priority rating (1-5) to *key*."""
    if not key:
        raise ValueError("key must not be empty")
    if not (MIN_RATING <= rating <= MAX_RATING):
        raise ValueError(f"rating must be between {MIN_RATING} and {MAX_RATING}")
    ratings = load_ratings(vault_path)
    ratings[key] = rating
    save_ratings(vault_path, ratings)


def remove_rating(vault_path: str, key: str) -> bool:
    """Remove rating for *key*. Returns True if entry existed."""
    ratings = load_ratings(vault_path)
    if key not in ratings:
        return False
    del ratings[key]
    save_ratings(vault_path, ratings)
    return True


def get_rating(vault_path: str, key: str) -> Optional[int]:
    """Return the rating for *key*, or None if not set."""
    return load_ratings(vault_path).get(key)


def keys_by_rating(vault_path: str, rating: int) -> list[str]:
    """Return sorted list of keys that have exactly *rating*."""
    return sorted(k for k, v in load_ratings(vault_path).items() if v == rating)


def top_keys(vault_path: str, n: int = 5) -> list[str]:
    """Return up to *n* keys with the highest ratings, sorted by rating desc then key."""
    ratings = load_ratings(vault_path)
    ranked = sorted(ratings.items(), key=lambda kv: (-kv[1], kv[0]))
    return [k for k, _ in ranked[:n]]
