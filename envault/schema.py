"""Key schema validation: enforce type, format, and required constraints on vault keys."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_VALID_TYPES = {"string", "integer", "boolean", "url", "email"}

_TYPE_PATTERNS: dict[str, re.Pattern[str]] = {
    "integer": re.compile(r"^-?\d+$"),
    "boolean": re.compile(r"^(true|false|1|0|yes|no)$", re.IGNORECASE),
    "url": re.compile(r"^https?://[^\s]+$"),
    "email": re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
}


def _schema_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".schema.json")


def load_schema(vault_path: Path) -> dict[str, dict[str, Any]]:
    path = _schema_path(vault_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_schema(vault_path: Path, schema: dict[str, dict[str, Any]]) -> None:
    _schema_path(vault_path).write_text(json.dumps(schema, indent=2))


def set_rule(vault_path: Path, key: str, *, type: str | None = None, required: bool | None = None, pattern: str | None = None) -> None:
    if not key:
        raise ValueError("key must not be empty")
    if type is not None and type not in _VALID_TYPES:
        raise ValueError(f"unknown type '{type}'; valid types: {sorted(_VALID_TYPES)}")
    if pattern is not None:
        re.compile(pattern)  # validate regex
    schema = load_schema(vault_path)
    entry: dict[str, Any] = schema.get(key, {})
    if type is not None:
        entry["type"] = type
    if required is not None:
        entry["required"] = required
    if pattern is not None:
        entry["pattern"] = pattern
    schema[key] = entry
    save_schema(vault_path, schema)


def remove_rule(vault_path: Path, key: str) -> bool:
    schema = load_schema(vault_path)
    if key not in schema:
        return False
    del schema[key]
    save_schema(vault_path, schema)
    return True


@dataclass
class SchemaViolation:
    key: str
    reason: str

    def __str__(self) -> str:
        return f"{self.key}: {self.reason}"


def validate_vault(vault_path: Path, vault_keys: set[str], plaintext_values: dict[str, str]) -> list[SchemaViolation]:
    """Validate decrypted values against the schema rules.

    Args:
        vault_path: path to the vault file.
        vault_keys: set of keys currently present in the vault.
        plaintext_values: mapping of key -> decrypted value for validation.
    """
    schema = load_schema(vault_path)
    violations: list[SchemaViolation] = []

    for key, rule in schema.items():
        required = rule.get("required", False)
        if required and key not in vault_keys:
            violations.append(SchemaViolation(key=key, reason="required key is missing from vault"))
            continue

        value = plaintext_values.get(key)
        if value is None:
            continue

        expected_type = rule.get("type")
        if expected_type and expected_type in _TYPE_PATTERNS:
            if not _TYPE_PATTERNS[expected_type].match(value):
                violations.append(SchemaViolation(key=key, reason=f"value does not match type '{expected_type}'"))

        custom_pattern = rule.get("pattern")
        if custom_pattern and not re.search(custom_pattern, value):
            violations.append(SchemaViolation(key=key, reason=f"value does not match pattern '{custom_pattern}'"))

    return violations
