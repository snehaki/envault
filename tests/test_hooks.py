"""Tests for envault/hooks.py"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envault.hooks import (
    load_hooks, save_hooks, add_hook, remove_hook, run_hooks,
    VALID_EVENTS, _hooks_path,
)


@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    vp = tmp_path / "vault.json"
    vp.write_text("{}")
    return vp


def test_load_hooks_returns_empty_when_no_file(vault_path):
    assert load_hooks(vault_path) == {}


def test_save_and_load_hooks_roundtrip(vault_path):
    hooks = {"post-set": ["echo hello"], "pre-export": ["make lint"]}
    save_hooks(vault_path, hooks)
    loaded = load_hooks(vault_path)
    assert loaded == hooks


def test_load_hooks_ignores_unknown_events(vault_path):
    path = _hooks_path(vault_path)
    path.write_text(json.dumps({"post-set": ["echo ok"], "unknown-event": ["echo bad"]}))
    loaded = load_hooks(vault_path)
    assert "unknown-event" not in loaded
    assert "post-set" in loaded


def test_add_hook_creates_entry(vault_path):
    add_hook(vault_path, "post-set", "echo done")
    hooks = load_hooks(vault_path)
    assert "echo done" in hooks["post-set"]


def test_add_hook_deduplicates(vault_path):
    add_hook(vault_path, "post-set", "echo done")
    add_hook(vault_path, "post-set", "echo done")
    hooks = load_hooks(vault_path)
    assert hooks["post-set"].count("echo done") == 1


def test_add_hook_multiple_commands(vault_path):
    add_hook(vault_path, "pre-export", "make check")
    add_hook(vault_path, "pre-export", "make lint")
    hooks = load_hooks(vault_path)
    assert len(hooks["pre-export"]) == 2


def test_add_hook_invalid_event_raises(vault_path):
    with pytest.raises(ValueError, match="Unknown event"):
        add_hook(vault_path, "on-magic", "echo oops")


def test_remove_hook_returns_true_when_found(vault_path):
    add_hook(vault_path, "post-set", "echo hello")
    result = remove_hook(vault_path, "post-set", "echo hello")
    assert result is True
    hooks = load_hooks(vault_path)
    assert "post-set" not in hooks


def test_remove_hook_returns_false_when_not_found(vault_path):
    result = remove_hook(vault_path, "post-set", "echo missing")
    assert result is False


def test_remove_hook_leaves_other_commands(vault_path):
    add_hook(vault_path, "post-set", "cmd-a")
    add_hook(vault_path, "post-set", "cmd-b")
    remove_hook(vault_path, "post-set", "cmd-a")
    hooks = load_hooks(vault_path)
    assert hooks["post-set"] == ["cmd-b"]


def test_run_hooks_calls_subprocess(vault_path):
    add_hook(vault_path, "post-set", "echo triggered")
    mock_result = MagicMock(returncode=0)
    with patch("envault.hooks.subprocess.run", return_value=mock_result) as mock_run:
        results = run_hooks(vault_path, "post-set")
    mock_run.assert_called_once_with("echo triggered", shell=True, env=None)
    assert results == [("echo triggered", 0)]


def test_run_hooks_returns_empty_for_no_hooks(vault_path):
    results = run_hooks(vault_path, "pre-get")
    assert results == []
