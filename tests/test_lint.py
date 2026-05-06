"""Tests for envault.lint module."""

import pytest

from envault.crypto import encrypt
from envault.lint import lint_vault, LintIssue

PASS = "testpass"


def _make_vault(*pairs) -> dict:
    """Build a minimal vault dict from (key, plaintext) pairs."""
    keys = {k: encrypt(v, PASS) for k, v in pairs}
    return {'keys': keys}


def test_lint_clean_vault_has_no_issues():
    vault = _make_vault(("DATABASE_URL", "postgres://localhost/db"))
    result = lint_vault(vault, PASS)
    assert result.ok
    assert result.issues == []


def test_lint_empty_vault_has_no_issues():
    result = lint_vault({'keys': {}}, PASS)
    assert result.ok
    assert result.issues == []


def test_lint_lowercase_key_raises_warning():
    vault = _make_vault(("database_url", "postgres://localhost/db"))
    result = lint_vault(vault, PASS)
    warnings = [i for i in result.warnings if "UPPER_SNAKE_CASE" in i.message]
    assert len(warnings) == 1
    assert warnings[0].key == "database_url"


def test_lint_mixed_case_key_raises_warning():
    vault = _make_vault(("MyKey", "value"))
    result = lint_vault(vault, PASS)
    assert any("UPPER_SNAKE_CASE" in i.message for i in result.warnings)


def test_lint_empty_value_raises_warning():
    vault = _make_vault(("API_KEY", ""))
    result = lint_vault(vault, PASS)
    assert any("empty" in i.message for i in result.warnings)
    assert result.ok  # empty value is warning, not error


def test_lint_placeholder_value_raises_warning():
    vault = _make_vault(("REDIS_URL", "redis://${REDIS_HOST}:6379"))
    result = lint_vault(vault, PASS)
    assert any("placeholder" in i.message for i in result.warnings)


def test_lint_angle_bracket_placeholder_raises_warning():
    vault = _make_vault(("SECRET_KEY", "<MY_SECRET>"))
    result = lint_vault(vault, PASS)
    assert any("placeholder" in i.message for i in result.warnings)


def test_lint_short_secret_raises_warning():
    vault = _make_vault(("DB_PASSWORD", "abc"))
    result = lint_vault(vault, PASS)
    assert any("short" in i.message for i in result.warnings)


def test_lint_short_non_secret_key_no_warning():
    vault = _make_vault(("APP_ENV", "dev"))
    result = lint_vault(vault, PASS)
    # 'dev' is short but key doesn't match secret pattern
    short_warnings = [i for i in result.warnings if "short" in i.message]
    assert short_warnings == []


def test_lint_corrupt_value_is_error():
    vault = {'keys': {'BAD_KEY': 'not-valid-ciphertext'}}
    result = lint_vault(vault, PASS)
    assert not result.ok
    errors = [i for i in result.errors if "decrypt" in i.message]
    assert len(errors) == 1
    assert errors[0].key == 'BAD_KEY'


def test_lint_result_ok_false_when_errors():
    vault = {'keys': {'BROKEN': 'garbage'}}
    result = lint_vault(vault, PASS)
    assert not result.ok


def test_lint_issue_str_format():
    issue = LintIssue(key='FOO', severity='warning', message='Some problem.')
    assert str(issue) == '[WARNING] FOO: Some problem.'


def test_lint_multiple_keys_multiple_issues():
    vault = _make_vault(
        ("GOOD_KEY", "long-enough-value"),
        ("bad_key", ""),
    )
    result = lint_vault(vault, PASS)
    keys_with_issues = {i.key for i in result.issues}
    assert "bad_key" in keys_with_issues
    assert "GOOD_KEY" not in keys_with_issues
