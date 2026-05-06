"""Tests for envault.ttl — key expiry / TTL support."""

from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta

import pytest

from envault.ttl import (
    set_ttl,
    get_ttl,
    remove_ttl,
    is_expired,
    purge_expired,
    list_ttls,
)


@pytest.fixture()
def vault():
    return {"KEY": "enc_value", "OTHER": "enc_other"}


def test_set_ttl_stores_iso_timestamp(vault):
    set_ttl(vault, "KEY", 60)
    assert "_ttl" in vault
    assert "KEY" in vault["_ttl"]
    dt = datetime.fromisoformat(vault["_ttl"]["KEY"])
    assert dt.tzinfo is not None


def test_get_ttl_returns_datetime(vault):
    set_ttl(vault, "KEY", 120)
    result = get_ttl(vault, "KEY")
    assert isinstance(result, datetime)


def test_get_ttl_returns_none_when_not_set(vault):
    assert get_ttl(vault, "KEY") is None


def test_set_ttl_raises_for_non_positive_seconds(vault):
    with pytest.raises(ValueError):
        set_ttl(vault, "KEY", 0)
    with pytest.raises(ValueError):
        set_ttl(vault, "KEY", -10)


def test_remove_ttl_clears_entry(vault):
    set_ttl(vault, "KEY", 60)
    remove_ttl(vault, "KEY")
    assert get_ttl(vault, "KEY") is None


def test_remove_ttl_removes_section_when_empty(vault):
    set_ttl(vault, "KEY", 60)
    remove_ttl(vault, "KEY")
    assert "_ttl" not in vault


def test_is_expired_false_for_future_ttl(vault):
    set_ttl(vault, "KEY", 3600)
    assert is_expired(vault, "KEY") is False


def test_is_expired_true_for_past_ttl(vault):
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    vault.setdefault("_ttl", {})["KEY"] = past
    assert is_expired(vault, "KEY") is True


def test_is_expired_false_when_no_ttl(vault):
    assert is_expired(vault, "KEY") is False


def test_purge_expired_removes_expired_keys(vault):
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    vault["_ttl"] = {"KEY": past}
    removed = purge_expired(vault)
    assert "KEY" in removed
    assert "KEY" not in vault
    assert "_ttl" not in vault


def test_purge_expired_keeps_live_keys(vault):
    set_ttl(vault, "KEY", 3600)
    removed = purge_expired(vault)
    assert removed == []
    assert "KEY" in vault


def test_list_ttls_returns_all_entries(vault):
    set_ttl(vault, "KEY", 60)
    set_ttl(vault, "OTHER", 120)
    ttls = list_ttls(vault)
    assert set(ttls.keys()) == {"KEY", "OTHER"}
    assert all(isinstance(v, datetime) for v in ttls.values())


def test_list_ttls_empty_when_no_ttls(vault):
    assert list_ttls(vault) == {}
