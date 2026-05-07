"""CLI commands for managing per-vault key quotas."""

from __future__ import annotations

from pathlib import Path

import click

from envault.quota import get_limit, set_limit, remove_limit
from envault.vault import get_default_vault_path


@click.group("quota")
def quota_group() -> None:
    """Manage key quota settings for a vault."""


@quota_group.command("set")
@click.argument("limit", type=int)
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_quota_set(limit: int, vault: str | None) -> None:
    """Set the maximum number of keys allowed in the vault."""
    vault_path = Path(vault) if vault else get_default_vault_path()
    try:
        set_limit(vault_path, limit)
        click.echo(f"Quota set: maximum {limit} keys.")
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@quota_group.command("show")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_quota_show(vault: str | None) -> None:
    """Show the current quota limit."""
    vault_path = Path(vault) if vault else get_default_vault_path()
    limit = get_limit(vault_path)
    click.echo(f"Key quota limit: {limit}")


@quota_group.command("remove")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_quota_remove(vault: str | None) -> None:
    """Remove the quota limit (revert to default)."""
    vault_path = Path(vault) if vault else get_default_vault_path()
    removed = remove_limit(vault_path)
    if removed:
        click.echo("Quota limit removed.")
    else:
        click.echo("No quota limit was set.")
