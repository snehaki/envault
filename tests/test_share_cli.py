"""Integration tests for the share CLI commands."""

from __future__ import annotations

import json
import os
import pytest

from click.testing import CliRunner

from envault.cli_share import share_group
from envault.crypto import decrypt, encrypt
from envault.vault import save_vault


SRC_PASS = "src-pass"
BUNDLE_PASS = "bundle-pass"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / ".envault")
    vault = {
        "SECRET": encrypt("topsecret", SRC_PASS),
        "TOKEN": encrypt("mytoken", SRC_PASS),
    }
    save_vault(path, vault)
    return path


def test_share_export_creates_bundle_file(runner, vault_file, tmp_path):
    out = str(tmp_path / "out.bundle")
    result = runner.invoke(
        share_group,
        ["export", "--vault", vault_file, "--out", out],
        input=f"{SRC_PASS}\n{BUNDLE_PASS}\n{BUNDLE_PASS}\n",
    )
    assert result.exit_code == 0, result.output
    assert os.path.exists(out)
    assert "2 keys" in result.output


def test_share_export_import_roundtrip(runner, vault_file, tmp_path):
    bundle_path = str(tmp_path / "vault.bundle")
    dest_vault = str(tmp_path / ".envault_dest")
    dest_pass = "dest-pass"

    runner.invoke(
        share_group,
        ["export", "--vault", vault_file, "--out", bundle_path],
        input=f"{SRC_PASS}\n{BUNDLE_PASS}\n{BUNDLE_PASS}\n",
    )

    result = runner.invoke(
        share_group,
        ["import", bundle_path, "--vault", dest_vault],
        input=f"{BUNDLE_PASS}\n{dest_pass}\n",
    )
    assert result.exit_code == 0, result.output
    assert os.path.exists(dest_vault)

    with open(dest_vault) as fh:
        imported_vault = json.load(fh)

    assert decrypt(imported_vault["SECRET"], dest_pass) == "topsecret"
    assert decrypt(imported_vault["TOKEN"], dest_pass) == "mytoken"


def test_share_import_wrong_bundle_pass_fails(runner, vault_file, tmp_path):
    bundle_path = str(tmp_path / "vault.bundle")
    dest_vault = str(tmp_path / ".envault_dest")

    runner.invoke(
        share_group,
        ["export", "--vault", vault_file, "--out", bundle_path],
        input=f"{SRC_PASS}\n{BUNDLE_PASS}\n{BUNDLE_PASS}\n",
    )

    result = runner.invoke(
        share_group,
        ["import", bundle_path, "--vault", dest_vault],
        input=f"wrong-pass\ndest-pass\n",
    )
    assert result.exit_code != 0 or "Error" in result.output
