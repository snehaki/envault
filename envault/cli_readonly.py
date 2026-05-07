"""CLI commands for managing read-only key locks."""

from __future__ import annotations

import click

from envault.readonly import lock_key, unlock_key, is_locked, list_locked
from envault.vault import get_default_vault_path


@click.group("readonly", help="Lock or unlock keys to prevent accidental overwrites.")
def readonly_group() -> None:  # pragma: no cover
    pass


@readonly_group.command("lock")
@click.argument("key")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_lock(key: str, vault: str | None) -> None:
    """Mark KEY as read-only."""
    vault_path = vault or get_default_vault_path()
    try:
        lock_key(vault_path, key)
        click.echo(f"Locked: {key}")
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@readonly_group.command("unlock")
@click.argument("key")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_unlock(key: str, vault: str | None) -> None:
    """Remove the read-only lock from KEY."""
    vault_path = vault or get_default_vault_path()
    removed = unlock_key(vault_path, key)
    if removed:
        click.echo(f"Unlocked: {key}")
    else:
        click.echo(f"{key} was not locked.")


@readonly_group.command("check")
@click.argument("key")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_check(key: str, vault: str | None) -> None:
    """Print whether KEY is locked."""
    vault_path = vault or get_default_vault_path()
    if is_locked(vault_path, key):
        click.echo(f"{key} is locked (read-only).")
    else:
        click.echo(f"{key} is not locked.")


@readonly_group.command("list")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_list(vault: str | None) -> None:
    """List all locked keys."""
    vault_path = vault or get_default_vault_path()
    keys = list_locked(vault_path)
    if not keys:
        click.echo("No keys are locked.")
    else:
        for key in keys:
            click.echo(key)
