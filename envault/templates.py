"""Template support: save and apply named sets of keys as templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


def _templates_path(vault_path: Path) -> Path:
    """Return the path to the templates file alongside the vault."""
    return vault_path.parent / (vault_path.stem + ".templates.json")


def load_templates(vault_path: Path) -> Dict[str, List[str]]:
    """Load all saved templates. Returns a dict of name -> list of keys."""
    path = _templates_path(vault_path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_templates(vault_path: Path, templates: Dict[str, List[str]]) -> None:
    """Persist templates to disk."""
    path = _templates_path(vault_path)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(templates, fh, indent=2, sort_keys=True)


def create_template(vault_path: Path, name: str, keys: List[str]) -> None:
    """Create or overwrite a named template with the given key names."""
    if not name:
        raise ValueError("Template name must not be empty.")
    if not keys:
        raise ValueError("Template must contain at least one key.")
    templates = load_templates(vault_path)
    templates[name] = sorted(set(keys))
    save_templates(vault_path, templates)


def delete_template(vault_path: Path, name: str) -> None:
    """Remove a named template. Raises KeyError if it does not exist."""
    templates = load_templates(vault_path)
    if name not in templates:
        raise KeyError(f"Template '{name}' not found.")
    del templates[name]
    save_templates(vault_path, templates)


def list_templates(vault_path: Path) -> List[str]:
    """Return sorted list of template names."""
    return sorted(load_templates(vault_path).keys())


def apply_template(
    vault_path: Path,
    name: str,
    vault: Dict,
    passphrase: str,
    default: Optional[str] = "",
) -> List[str]:
    """Return the list of key names defined by the template that exist in vault.

    Missing keys are noted but not created; returns list of present keys.
    """
    templates = load_templates(vault_path)
    if name not in templates:
        raise KeyError(f"Template '{name}' not found.")
    template_keys = templates[name]
    present = [k for k in template_keys if k in vault.get("keys", {})]
    return present
