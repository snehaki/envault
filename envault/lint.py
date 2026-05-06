"""Lint/validate vault keys and values for common issues."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from envault.crypto import decrypt

# Keys should be UPPER_SNAKE_CASE
_VALID_KEY_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')
# Warn if a value looks like it might be an unresolved template placeholder
_PLACEHOLDER_RE = re.compile(r'\$\{[^}]+\}|<[A-Z_]+>')
# Warn on suspiciously short secrets (< 8 chars) for keys that look like passwords/tokens
_SECRET_KEY_RE = re.compile(r'(PASSWORD|SECRET|TOKEN|KEY|PASS)', re.IGNORECASE)


@dataclass
class LintIssue:
    key: str
    severity: str  # 'error' | 'warning'
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == 'error']

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == 'warning']

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def lint_vault(vault: dict, passphrase: str) -> LintResult:
    """Run all lint checks against a vault dict. Returns a LintResult."""
    result = LintResult()
    encrypted_keys: dict = vault.get('keys', {})

    if not encrypted_keys:
        return result

    for key in encrypted_keys:
        # Check key naming convention
        if not _VALID_KEY_RE.match(key):
            result.issues.append(LintIssue(
                key=key,
                severity='warning',
                message="Key does not follow UPPER_SNAKE_CASE convention.",
            ))

        # Decrypt and inspect value
        try:
            value = decrypt(encrypted_keys[key], passphrase)
        except Exception:
            result.issues.append(LintIssue(
                key=key,
                severity='error',
                message="Failed to decrypt value — vault may be corrupt or passphrase is wrong.",
            ))
            continue

        if not value:
            result.issues.append(LintIssue(
                key=key,
                severity='warning',
                message="Value is empty.",
            ))
            continue

        if _PLACEHOLDER_RE.search(value):
            result.issues.append(LintIssue(
                key=key,
                severity='warning',
                message="Value appears to contain an unresolved placeholder.",
            ))

        if _SECRET_KEY_RE.search(key) and len(value) < 8:
            result.issues.append(LintIssue(
                key=key,
                severity='warning',
                message="Secret value is suspiciously short (< 8 characters).",
            ))

    return result
