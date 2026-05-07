"""Unit tests for envault.quota."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.quota import (
    _DEFAULT_LIMIT,
    _quota_path,
    check_quota,
    get_limit,
    load_quota,
    remove_limit,
    set_limit,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "test.vault"


def test_sidecar_uses_quotas_suffix(vault_path: Path) -> None:
    assert _quota_path(vault_path).suffix == ".quotas"


def test_sidecar_not_created_until_first_set(vault_path: Path) -> None:
    assert not _quota_path(vault_path).exists()


def test_set_limit_persists(vault_path: Path) -> None:
    set_limit(vault_path, 50)
    assert _quota_path(vault_path).exists()
    assert get_limit(vault_path) == 50


def test_sidecar_is_valid_json(vault_path: Path) -> None:
    set_limit(vault_path, 20)
    data = json.loads(_quota_path(vault_path).read_text())
    assert "limit" in data


def test_set_limit_raises_for_non_positive(vault_path: Path) -> None:
    with pytest.raises(ValueError, match="positive"):
        set_limit(vault_path, 0)
    with pytest.raises(ValueError):
        set_limit(vault_path, -5)


def test_get_limit_returns_default_when_not_set(vault_path: Path) -> None:
    assert get_limit(vault_path) == _DEFAULT_LIMIT


def test_get_limit_returns_set_value(vault_path: Path) -> None:
    set_limit(vault_path, 75)
    assert get_limit(vault_path) == 75


def test_remove_limit_returns_true_when_removed(vault_path: Path) -> None:
    set_limit(vault_path, 10)
    assert remove_limit(vault_path) is True


def test_remove_limit_returns_false_when_not_set(vault_path: Path) -> None:
    assert remove_limit(vault_path) is False


def test_remove_limit_reverts_to_default(vault_path: Path) -> None:
    set_limit(vault_path, 10)
    remove_limit(vault_path)
    assert get_limit(vault_path) == _DEFAULT_LIMIT


def test_check_quota_returns_none_when_under_limit(vault_path: Path) -> None:
    set_limit(vault_path, 10)
    assert check_quota(vault_path, 9) is None


def test_check_quota_returns_message_at_limit(vault_path: Path) -> None:
    set_limit(vault_path, 5)
    msg = check_quota(vault_path, 5)
    assert msg is not None
    assert "5/5" in msg


def test_check_quota_returns_message_over_limit(vault_path: Path) -> None:
    set_limit(vault_path, 3)
    msg = check_quota(vault_path, 10)
    assert msg is not None
    assert "exceeded" in msg.lower()


def test_load_quota_returns_empty_when_no_file(vault_path: Path) -> None:
    assert load_quota(vault_path) == {}
