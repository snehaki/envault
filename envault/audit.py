"""Audit log helpers — record when secrets are accessed or modified."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

Action = Literal["get", "set", "delete", "export", "import"]


def _audit_path(vault_path: Path) -> Path:
    """Return the audit log path next to the vault file."""
    return vault_path.with_suffix(".audit.jsonl")


def record(vault_path: Path, action: Action, key: str | None = None) -> None:
    """Append a single audit entry to the log file."""
    entry = {
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "action": action,
    }
    if key is not None:
        entry["key"] = key

    audit_path = _audit_path(vault_path)
    with audit_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def read_log(vault_path: Path) -> list[dict]:
    """Return all audit entries for a vault, oldest first."""
    audit_path = _audit_path(vault_path)
    if not audit_path.exists():
        return []

    entries: list[dict] = []
    for line in audit_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def format_log(entries: list[dict]) -> str:
    """Return a human-readable audit log string."""
    if not entries:
        return "No audit entries found."

    rows: list[str] = []
    for e in entries:
        key_part = f"  key={e['key']}" if "key" in e else ""
        rows.append(f"{e['ts']}  {e['action']:<8}{key_part}")
    return "\n".join(rows)
