"""CLI commands for managing key aliases."""

from __future__ import annotations

import click

from envault.alias import (
    list_aliases,
    remove_alias,
    resolve_alias,
    set_alias,
)
from envault.vault import get_default_vault_path


@click.group("alias", help="Manage short aliases for vault keys.")
def alias_group() -> None:  # pragma: no cover
    pass


@alias_group.command("set")
@click.argument("alias")
@click.argument("key")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_alias_set(alias: str, key: str, vault: str | None) -> None:
    """Map ALIAS to KEY."""
    vault_path = vault or get_default_vault_path()
    try:
        set_alias(vault_path, alias, key)
        click.echo(f"Alias '{alias}' -> '{key}' saved.")
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@alias_group.command("remove")
@click.argument("alias")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_alias_remove(alias: str, vault: str | None) -> None:
    """Remove ALIAS."""
    vault_path = vault or get_default_vault_path()
    removed = remove_alias(vault_path, alias)
    if removed:
        click.echo(f"Alias '{alias}' removed.")
    else:
        raise click.ClickException(f"Alias '{alias}' not found.")


@alias_group.command("list")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_alias_list(vault: str | None) -> None:
    """List all defined aliases."""
    vault_path = vault or get_default_vault_path()
    aliases = list_aliases(vault_path)
    if not aliases:
        click.echo("No aliases defined.")
        return
    for alias, key in aliases.items():
        click.echo(f"  {alias}  ->  {key}")


@alias_group.command("resolve")
@click.argument("alias")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_alias_resolve(alias: str, vault: str | None) -> None:
    """Print the key that ALIAS maps to."""
    vault_path = vault or get_default_vault_path()
    key = resolve_alias(vault_path, alias)
    if key is None:
        raise click.ClickException(f"Alias '{alias}' not found.")
    click.echo(key)
