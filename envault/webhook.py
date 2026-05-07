"""Webhook notification support for envault.

Allows registering HTTP endpoints that receive POST notifications
when vault keys are created, updated, or deleted.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Sidecar path
# ---------------------------------------------------------------------------

VALID_EVENTS = {"set", "delete", "rotate", "import"}


def _webhooks_path(vault_path: Path) -> Path:
    """Return the sidecar path for webhook registrations."""
    return vault_path.with_suffix(".webhooks.json")


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def load_webhooks(vault_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Load webhook registrations from the sidecar file.

    Returns a mapping of event -> list of webhook entries.
    Each entry has at minimum a ``url`` key.
    """
    path = _webhooks_path(vault_path)
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if k in VALID_EVENTS}


def save_webhooks(vault_path: Path, webhooks: dict[str, list[dict[str, Any]]]) -> None:
    """Persist webhook registrations to the sidecar file."""
    path = _webhooks_path(vault_path)
    path.write_text(json.dumps(webhooks, indent=2))


# ---------------------------------------------------------------------------
# Management helpers
# ---------------------------------------------------------------------------

def add_webhook(vault_path: Path, event: str, url: str, secret: str | None = None) -> None:
    """Register *url* to receive notifications for *event*.

    Args:
        vault_path: Path to the vault file.
        event: One of the VALID_EVENTS strings.
        url: The HTTP(S) endpoint to POST to.
        secret: Optional shared secret stored alongside the URL.

    Raises:
        ValueError: If *event* is not a recognised event name or *url* is empty.
    """
    if event not in VALID_EVENTS:
        raise ValueError(f"Unknown event '{event}'. Valid events: {sorted(VALID_EVENTS)}")
    if not url:
        raise ValueError("url must not be empty")

    webhooks = load_webhooks(vault_path)
    entries = webhooks.setdefault(event, [])

    # Avoid duplicate URLs for the same event
    if any(e["url"] == url for e in entries):
        return

    entry: dict[str, Any] = {"url": url}
    if secret:
        entry["secret"] = secret
    entries.append(entry)
    save_webhooks(vault_path, webhooks)


def remove_webhook(vault_path: Path, event: str, url: str) -> bool:
    """Remove a webhook registration.

    Returns True if the entry was found and removed, False otherwise.
    """
    webhooks = load_webhooks(vault_path)
    entries = webhooks.get(event, [])
    new_entries = [e for e in entries if e["url"] != url]
    if len(new_entries) == len(entries):
        return False
    webhooks[event] = new_entries
    if not webhooks[event]:
        del webhooks[event]
    save_webhooks(vault_path, webhooks)
    return True


def list_webhooks(vault_path: Path) -> dict[str, list[str]]:
    """Return a mapping of event -> list of registered URLs."""
    webhooks = load_webhooks(vault_path)
    return {event: [e["url"] for e in entries] for event, entries in webhooks.items()}


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def dispatch(vault_path: Path, event: str, payload: dict[str, Any]) -> list[str]:
    """Fire all webhooks registered for *event*.

    Sends a JSON POST request to each registered URL.  Failures are collected
    and returned as a list of error strings rather than raised, so that a
    single failing endpoint does not block the rest.

    Args:
        vault_path: Path to the vault file.
        event: The event that occurred.
        payload: Arbitrary JSON-serialisable data to include in the body.

    Returns:
        A list of error messages (empty list means all requests succeeded).
    """
    webhooks = load_webhooks(vault_path)
    entries = webhooks.get(event, [])
    errors: list[str] = []

    body = json.dumps({"event": event, **payload}).encode()
    for entry in entries:
        url = entry["url"]
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5):
                pass
        except urllib.error.URLError as exc:
            errors.append(f"{url}: {exc}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{url}: unexpected error: {exc}")

    return errors
