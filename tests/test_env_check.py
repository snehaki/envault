"""Tests for envault.env_check and the CLI check command."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.env_check import CheckResult, check_vault, parse_example_keys
from envault.cli_env_check import check_group


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_example(tmp_path: Path, content: str) -> Path:
    p = tmp_path / ".env.example"
    p.write_text(content)
    return p


def _write_vault(tmp_path: Path, keys: list[str]) -> Path:
    vault = {"keys": {k: "enc_placeholder" for k in keys}}
    p = tmp_path / ".envault.json"
    p.write_text(json.dumps(vault))
    return p


# ---------------------------------------------------------------------------
# parse_example_keys
# ---------------------------------------------------------------------------

def test_parse_example_keys_basic(tmp_path):
    p = _write_example(tmp_path, "DB_URL=\nSECRET_KEY=\n")
    assert parse_example_keys(p) == {"DB_URL", "SECRET_KEY"}


def test_parse_example_keys_ignores_comments(tmp_path):
    p = _write_example(tmp_path, "# comment\nAPI_KEY=\n")
    assert parse_example_keys(p) == {"API_KEY"}


def test_parse_example_keys_ignores_blank_lines(tmp_path):
    p = _write_example(tmp_path, "\n  \nFOO=bar\n")
    assert parse_example_keys(p) == {"FOO"}


# ---------------------------------------------------------------------------
# check_vault
# ---------------------------------------------------------------------------

def test_check_vault_ok(tmp_path):
    p = _write_example(tmp_path, "FOO=\nBAR=\n")
    vault = {"keys": {"FOO": "x", "BAR": "y"}}
    result = check_vault(vault, p)
    assert result.ok


def test_check_vault_missing(tmp_path):
    p = _write_example(tmp_path, "FOO=\nBAR=\nBAZ=\n")
    vault = {"keys": {"FOO": "x"}}
    result = check_vault(vault, p)
    assert "BAR" in result.missing_in_vault
    assert "BAZ" in result.missing_in_vault
    assert not result.ok


def test_check_vault_extra(tmp_path):
    p = _write_example(tmp_path, "FOO=\n")
    vault = {"keys": {"FOO": "x", "EXTRA": "y"}}
    result = check_vault(vault, p)
    assert "EXTRA" in result.extra_in_vault
    assert not result.ok


def test_check_vault_ignore_extra(tmp_path):
    p = _write_example(tmp_path, "FOO=\n")
    vault = {"keys": {"FOO": "x", "EXTRA": "y"}}
    result = check_vault(vault, p, ignore_extra=True)
    assert result.ok
    assert result.extra_in_vault == []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_check_ok(tmp_path, runner):
    example = _write_example(tmp_path, "FOO=\n")
    vault = _write_vault(tmp_path, ["FOO"])
    result = runner.invoke(check_group, ["run", str(example), "--vault", str(vault)])
    assert result.exit_code == 0
    assert "matches" in result.output


def test_cli_check_missing_reports(tmp_path, runner):
    example = _write_example(tmp_path, "FOO=\nBAR=\n")
    vault = _write_vault(tmp_path, ["FOO"])
    result = runner.invoke(check_group, ["run", str(example), "--vault", str(vault)])
    assert "MISSING" in result.output
    assert "BAR" in result.output


def test_cli_check_strict_exits_nonzero(tmp_path, runner):
    example = _write_example(tmp_path, "FOO=\nBAR=\n")
    vault = _write_vault(tmp_path, ["FOO"])
    result = runner.invoke(
        check_group, ["run", str(example), "--vault", str(vault), "--strict"]
    )
    assert result.exit_code != 0


def test_cli_check_missing_example_file(tmp_path, runner):
    vault = _write_vault(tmp_path, ["FOO"])
    result = runner.invoke(
        check_group, ["run", str(tmp_path / "no_such.env"), "--vault", str(vault)]
    )
    assert result.exit_code != 0
