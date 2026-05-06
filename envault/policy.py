"""Key policy enforcement: define and validate rules for secret keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

POLICY_SUFFIX = ".policies.json"


def _policies_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix("") .parent / (Path(vault_path).stem + POLICY_SUFFIX)


def load_policies(vault_path: str) -> dict[str, dict[str, Any]]:
    """Return {key: {rule: value}} mapping; empty dict if file missing."""
    p = _policies_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def save_policies(vault_path: str, policies: dict[str, dict[str, Any]]) -> None:
    p = _policies_path(vault_path)
    p.write_text(json.dumps(policies, indent=2))


def set_policy(vault_path: str, key: str, rule: str, value: Any) -> None:
    """Set a single rule for a key (e.g. min_length=8, required=True)."""
    _VALID_RULES = {"min_length", "max_length", "required", "pattern", "no_spaces"}
    if rule not in _VALID_RULES:
        raise ValueError(f"Unknown policy rule '{rule}'. Valid: {sorted(_VALID_RULES)}")
    policies = load_policies(vault_path)
    policies.setdefault(key, {})[rule] = value
    save_policies(vault_path, policies)


def remove_policy(vault_path: str, key: str) -> bool:
    """Remove all policies for a key. Returns True if key existed."""
    policies = load_policies(vault_path)
    if key not in policies:
        return False
    del policies[key]
    save_policies(vault_path, policies)
    return True


def get_policy(vault_path: str, key: str) -> dict[str, Any]:
    """Return policy rules for a single key."""
    return load_policies(vault_path).get(key, {})


def validate_value(key: str, value: str, rules: dict[str, Any]) -> list[str]:
    """Return list of violation messages; empty list means valid."""
    import re
    issues: list[str] = []
    if rules.get("required") and not value:
        issues.append(f"{key}: value is required but empty")
    min_len = rules.get("min_length")
    if min_len is not None and len(value) < int(min_len):
        issues.append(f"{key}: value length {len(value)} < min_length {min_len}")
    max_len = rules.get("max_length")
    if max_len is not None and len(value) > int(max_len):
        issues.append(f"{key}: value length {len(value)} > max_length {max_len}")
    pattern = rules.get("pattern")
    if pattern and not re.fullmatch(pattern, value):
        issues.append(f"{key}: value does not match pattern '{pattern}'")
    if rules.get("no_spaces") and " " in value:
        issues.append(f"{key}: value must not contain spaces")
    return issues
