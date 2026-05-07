"""CLI commands for key dependency management."""
from __future__ import annotations

import click

from envault.dependency import (
    get_dependents,
    load_dependencies,
    remove_dependency,
    resolve_order,
    set_dependency,
)
from envault.vault import get_default_vault_path


@click.group("dep")
def dependency_group() -> None:
    """Manage key dependencies."""


@dependency_group.command("set")
@click.argument("key")
@click.argument("depends_on", nargs=-1, required=True)
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_dep_set(key: str, depends_on: tuple, vault: str | None) -> None:
    """Declare that KEY depends on DEPENDS_ON keys."""
    vault_path = vault or get_default_vault_path()
    try:
        set_dependency(vault_path, key, list(depends_on))
        click.echo(f"Set: {key} depends on {', '.join(depends_on)}")
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@dependency_group.command("remove")
@click.argument("key")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_dep_remove(key: str, vault: str | None) -> None:
    """Remove dependency declaration for KEY."""
    vault_path = vault or get_default_vault_path()
    removed = remove_dependency(vault_path, key)
    if removed:
        click.echo(f"Removed dependency entry for '{key}'.")
    else:
        click.echo(f"No dependency entry found for '{key}'.")


@dependency_group.command("list")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_dep_list(vault: str | None) -> None:
    """List all declared dependencies."""
    vault_path = vault or get_default_vault_path()
    deps = load_dependencies(vault_path)
    if not deps:
        click.echo("No dependencies defined.")
        return
    for key, parents in sorted(deps.items()):
        click.echo(f"  {key} -> {', '.join(parents)}")


@dependency_group.command("dependents")
@click.argument("key")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_dep_dependents(key: str, vault: str | None) -> None:
    """Show keys that depend on KEY."""
    vault_path = vault or get_default_vault_path()
    dependents = get_dependents(vault_path, key)
    if not dependents:
        click.echo(f"No keys depend on '{key}'.")
    else:
        click.echo(f"Keys depending on '{key}':")
        for k in dependents:
            click.echo(f"  {k}")


@dependency_group.command("order")
@click.argument("keys", nargs=-1, required=True)
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_dep_order(keys: tuple, vault: str | None) -> None:
    """Print KEYS in topological (dependency-first) order."""
    vault_path = vault or get_default_vault_path()
    try:
        ordered = resolve_order(vault_path, list(keys))
        for k in ordered:
            click.echo(k)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
