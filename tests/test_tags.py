"""Tests for envault.tags — tag assignment, removal, and filtering."""

import pytest

from envault.tags import (
    TAGS_META_KEY,
    add_tag,
    all_tags,
    get_tags,
    keys_by_tag,
    purge_key,
    remove_tag,
    set_tags,
)


@pytest.fixture()
def vault():
    return {
        "DB_URL": "enc:abc",
        "API_KEY": "enc:def",
        "SECRET": "enc:ghi",
    }


def test_get_tags_returns_empty_for_untagged_key(vault):
    assert get_tags(vault, "DB_URL") == []


def test_set_tags_assigns_tags(vault):
    updated = set_tags(vault, "DB_URL", ["prod", "database"])
    assert get_tags(updated, "DB_URL") == ["database", "prod"]  # sorted


def test_set_tags_deduplicates(vault):
    updated = set_tags(vault, "API_KEY", ["prod", "prod", "external"])
    assert get_tags(updated, "API_KEY") == ["external", "prod"]


def test_set_tags_empty_list_removes_entry(vault):
    vault = set_tags(vault, "DB_URL", ["prod"])
    vault = set_tags(vault, "DB_URL", [])
    assert get_tags(vault, "DB_URL") == []
    assert "DB_URL" not in vault.get(TAGS_META_KEY, {})


def test_add_tag_appends_without_duplicates(vault):
    vault = add_tag(vault, "SECRET", "internal")
    vault = add_tag(vault, "SECRET", "internal")  # duplicate — should be ignored
    assert get_tags(vault, "SECRET") == ["internal"]


def test_add_tag_multiple_tags(vault):
    vault = add_tag(vault, "SECRET", "internal")
    vault = add_tag(vault, "SECRET", "prod")
    assert "internal" in get_tags(vault, "SECRET")
    assert "prod" in get_tags(vault, "SECRET")


def test_remove_tag_removes_existing(vault):
    vault = set_tags(vault, "API_KEY", ["prod", "external"])
    vault = remove_tag(vault, "API_KEY", "prod")
    assert get_tags(vault, "API_KEY") == ["external"]


def test_remove_tag_noop_when_absent(vault):
    vault = set_tags(vault, "API_KEY", ["external"])
    vault = remove_tag(vault, "API_KEY", "nonexistent")
    assert get_tags(vault, "API_KEY") == ["external"]


def test_keys_by_tag_returns_matching_keys(vault):
    vault = set_tags(vault, "DB_URL", ["prod", "database"])
    vault = set_tags(vault, "API_KEY", ["prod", "external"])
    vault = set_tags(vault, "SECRET", ["internal"])
    result = keys_by_tag(vault, "prod")
    assert result == ["API_KEY", "DB_URL"]


def test_keys_by_tag_empty_when_no_match(vault):
    assert keys_by_tag(vault, "nonexistent") == []


def test_all_tags_returns_sorted_unique(vault):
    vault = set_tags(vault, "DB_URL", ["prod", "database"])
    vault = set_tags(vault, "API_KEY", ["prod", "external"])
    assert all_tags(vault) == ["database", "external", "prod"]


def test_all_tags_empty_vault():
    assert all_tags({}) == []


def test_purge_key_removes_metadata(vault):
    vault = set_tags(vault, "DB_URL", ["prod"])
    vault = purge_key(vault, "DB_URL")
    assert get_tags(vault, "DB_URL") == []
    assert "DB_URL" not in vault.get(TAGS_META_KEY, {})


def test_purge_key_noop_when_no_metadata(vault):
    # Should not raise even if key never had tags
    purge_key(vault, "UNKNOWN_KEY")
