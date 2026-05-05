"""Integration-style tests: snapshot updated when vault changes via CLI."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.cli import cli
from envault.snapshot import load_snapshot, snapshot_path


PASSPHRASE = "integration-pass"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path):
    return tmp_path / ".envault"


def _run_set(runner, vault_file, key, value, passphrase=PASSPHRASE):
    return runner.invoke(
        cli,
        ["--vault", str(vault_file), "set", key, value],
        input=f"{passphrase}\n",
        catch_exceptions=False,
    )


def test_snapshot_file_created_after_set(runner, vault_file):
    result = _run_set(runner, vault_file, "MY_KEY", "my_value")
    assert result.exit_code == 0
    snap = snapshot_path(vault_file)
    assert snap.exists(), "snapshot file should be created alongside vault"


def test_snapshot_contains_set_key(runner, vault_file):
    _run_set(runner, vault_file, "TOKEN", "secret")
    snap = snapshot_path(vault_file)
    keys = load_snapshot(snap)
    assert "TOKEN" in keys


def test_snapshot_updated_on_second_set(runner, vault_file):
    _run_set(runner, vault_file, "FIRST", "v1")
    _run_set(runner, vault_file, "SECOND", "v2")
    snap = snapshot_path(vault_file)
    keys = load_snapshot(snap)
    assert "FIRST" in keys
    assert "SECOND" in keys
    assert keys == sorted(keys), "snapshot keys must be sorted"
