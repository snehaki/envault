"""Tests for envault.expiry."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.expiry import (
    get_expiry,
    is_expired,
    list_expiring,
    load_expiry,
    remove_expiry,
    set_expiry,
)
from envault.cli_expiry import expiry_group


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.envault")


def test_sidecar_uses_expiry_suffix(vault_path: str) -> None:
    set_expiry(vault_path, "KEY", 1)
    sidecar = Path(vault_path).with_suffix(".expiry.json")
    assert sidecar.exists()


def test_sidecar_not_created_until_first_set(vault_path: str) -> None:
    sidecar = Path(vault_path).with_suffix(".expiry.json")
    assert not sidecar.exists()


def test_set_expiry_persists(vault_path: str) -> None:
    set_expiry(vault_path, "MY_KEY", 7)
    data = load_expiry(vault_path)
    assert "MY_KEY" in data


def test_set_expiry_raises_for_non_positive_days(vault_path: str) -> None:
    with pytest.raises(ValueError):
        set_expiry(vault_path, "KEY", 0)
    with pytest.raises(ValueError):
        set_expiry(vault_path, "KEY", -5)


def test_get_expiry_returns_datetime(vault_path: str) -> None:
    set_expiry(vault_path, "KEY", 3)
    exp = get_expiry(vault_path, "KEY")
    assert isinstance(exp, datetime)


def test_get_expiry_returns_none_when_not_set(vault_path: str) -> None:
    assert get_expiry(vault_path, "MISSING") is None


def test_is_expired_false_for_future(vault_path: str) -> None:
    set_expiry(vault_path, "KEY", 10)
    assert not is_expired(vault_path, "KEY")


def test_is_expired_true_for_past(vault_path: str) -> None:
    # Manually write a past timestamp
    past = (datetime.now(timezone.utc) - timedelta(days=1)).replace(microsecond=0)
    sidecar = Path(vault_path).with_suffix(".expiry.json")
    sidecar.write_text(json.dumps({"OLD_KEY": past.isoformat()}))
    assert is_expired(vault_path, "OLD_KEY")


def test_remove_expiry_returns_true_when_removed(vault_path: str) -> None:
    set_expiry(vault_path, "KEY", 1)
    assert remove_expiry(vault_path, "KEY") is True
    assert get_expiry(vault_path, "KEY") is None


def test_remove_expiry_returns_false_when_missing(vault_path: str) -> None:
    assert remove_expiry(vault_path, "GHOST") is False


def test_list_expiring_sorted(vault_path: str) -> None:
    set_expiry(vault_path, "Z_KEY", 5)
    set_expiry(vault_path, "A_KEY", 2)
    entries = list_expiring(vault_path)
    keys = [e["key"] for e in entries]
    assert keys == ["A_KEY", "Z_KEY"]


def test_cli_set_and_list(vault_path: str) -> None:
    runner = CliRunner()
    result = runner.invoke(expiry_group, ["set", "DB_PASS", "30", "--vault", vault_path])
    assert result.exit_code == 0
    assert "DB_PASS" in result.output

    result = runner.invoke(expiry_group, ["list", "--vault", vault_path])
    assert result.exit_code == 0
    assert "DB_PASS" in result.output


def test_cli_check_not_expired(vault_path: str) -> None:
    runner = CliRunner()
    runner.invoke(expiry_group, ["set", "KEY", "10", "--vault", vault_path])
    result = runner.invoke(expiry_group, ["check", "KEY", "--vault", vault_path])
    assert result.exit_code == 0
    assert "OK" in result.output
