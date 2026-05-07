"""Sidecar file behaviour tests for quota."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.quota import _quota_path, set_limit


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "my.vault"


def test_sidecar_uses_quotas_suffix(vault_path: Path) -> None:
    sidecar = _quota_path(vault_path)
    assert sidecar.name.endswith(".quotas")


def test_sidecar_not_created_until_first_set(vault_path: Path) -> None:
    assert not _quota_path(vault_path).exists()


def test_sidecar_created_after_set(vault_path: Path) -> None:
    set_limit(vault_path, 30)
    assert _quota_path(vault_path).exists()


def test_sidecar_is_valid_json(vault_path: Path) -> None:
    set_limit(vault_path, 30)
    raw = _quota_path(vault_path).read_text()
    data = json.loads(raw)
    assert isinstance(data, dict)


def test_sidecar_stores_limit_field(vault_path: Path) -> None:
    set_limit(vault_path, 55)
    data = json.loads(_quota_path(vault_path).read_text())
    assert data["limit"] == 55


def test_sidecar_overwrite_updates_limit(vault_path: Path) -> None:
    set_limit(vault_path, 10)
    set_limit(vault_path, 99)
    data = json.loads(_quota_path(vault_path).read_text())
    assert data["limit"] == 99
