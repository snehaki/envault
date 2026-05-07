"""CLI commands for key expiry management."""
from __future__ import annotations

import click

from envault.expiry import (
    get_expiry,
    is_expired,
    list_expiring,
    remove_expiry,
    set_expiry,
)


@click.group("expiry")
def expiry_group() -> None:
    """Manage key expiry dates."""


@expiry_group.command("set")
@click.argument("key")
@click.argument("days", type=int)
@click.option("--vault", default=".envault", show_default=True, help="Vault file path.")
def cmd_expiry_set(key: str, days: int, vault: str) -> None:
    """Set KEY to expire in DAYS days."""
    try:
        exp = set_expiry(vault, key, days)
        click.echo(f"Expiry set: {key} expires at {exp.isoformat()}")
    except ValueError as exc:
        raise click.ClickException(str(exc))


@expiry_group.command("remove")
@click.argument("key")
@click.option("--vault", default=".envault", show_default=True)
def cmd_expiry_remove(key: str, vault: str) -> None:
    """Remove expiry for KEY."""
    removed = remove_expiry(vault, key)
    if removed:
        click.echo(f"Expiry removed for '{key}'.")
    else:
        click.echo(f"No expiry configured for '{key}'.")


@expiry_group.command("check")
@click.argument("key")
@click.option("--vault", default=".envault", show_default=True)
def cmd_expiry_check(key: str, vault: str) -> None:
    """Check whether KEY has expired."""
    exp = get_expiry(vault, key)
    if exp is None:
        click.echo(f"No expiry set for '{key}'.")
        return
    if is_expired(vault, key):
        click.echo(f"EXPIRED: '{key}' expired at {exp.isoformat()}")
    else:
        click.echo(f"OK: '{key}' expires at {exp.isoformat()}")


@expiry_group.command("list")
@click.option("--vault", default=".envault", show_default=True)
@click.option("--expired-only", is_flag=True, default=False, help="Show only expired keys.")
def cmd_expiry_list(vault: str, expired_only: bool) -> None:
    """List all keys with expiry dates."""
    entries = list_expiring(vault)
    if expired_only:
        entries = [e for e in entries if e["expired"]]
    if not entries:
        click.echo("No expiry entries found.")
        return
    for entry in entries:
        status = "EXPIRED" if entry["expired"] else "ok"
        click.echo(f"{entry['key']:<30} {entry['expires_at'].isoformat()}  [{status}]")
