"""CLI commands for managing key scopes."""
from __future__ import annotations

import click

from envault.scope import (
    get_scopes,
    keys_in_scope,
    remove_scope,
    set_scope,
    valid_scopes,
)
from envault.vault import get_default_vault_path


@click.group("scope")
def scope_group() -> None:
    """Manage environment scopes for vault keys."""


@scope_group.command("set")
@click.argument("key")
@click.argument("scopes", nargs=-1, required=True)
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_scope_set(key: str, scopes: tuple, vault: str | None) -> None:
    """Assign SCOPES to KEY (e.g. dev staging prod)."""
    vault_path = vault or get_default_vault_path()
    try:
        set_scope(vault_path, key, list(scopes))
        click.echo(f"Scopes for '{key}' set to: {', '.join(sorted(scopes))}")
    except ValueError as exc:
        raise click.ClickException(str(exc))


@scope_group.command("remove")
@click.argument("key")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_scope_remove(key: str, vault: str | None) -> None:
    """Remove scope restrictions from KEY."""
    vault_path = vault or get_default_vault_path()
    removed = remove_scope(vault_path, key)
    if removed:
        click.echo(f"Scopes removed for '{key}'.")
    else:
        click.echo(f"No scope entry found for '{key}'.")


@scope_group.command("show")
@click.argument("key")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_scope_show(key: str, vault: str | None) -> None:
    """Show scopes assigned to KEY."""
    vault_path = vault or get_default_vault_path()
    scopes = get_scopes(vault_path, key)
    if scopes:
        click.echo(f"{key}: {', '.join(scopes)}")
    else:
        click.echo(f"'{key}' has no scope restrictions (applies to all).")


@scope_group.command("list")
@click.argument("scope", required=False)
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_scope_list(scope: str | None, vault: str | None) -> None:
    """List keys in SCOPE, or show all valid scopes if none given."""
    if scope is None:
        click.echo("Valid scopes: " + ", ".join(valid_scopes()))
        return
    vault_path = vault or get_default_vault_path()
    keys = keys_in_scope(vault_path, scope)
    if keys:
        for k in keys:
            click.echo(k)
    else:
        click.echo(f"No keys found in scope '{scope}'.")
