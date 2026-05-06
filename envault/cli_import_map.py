"""CLI commands for managing import-maps in envault."""

from __future__ import annotations

import click

from envault.import_map import (
    load_map,
    set_entry,
    remove_entry,
)
from envault.vault import get_default_vault_path
from pathlib import Path


@click.group("map")
def map_group() -> None:
    """Manage key-rename import-maps."""


@map_group.command("set")
@click.argument("source_key")
@click.argument("target_key")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_map_set(source_key: str, target_key: str, vault: str | None) -> None:
    """Map SOURCE_KEY to TARGET_KEY on import."""
    vault_path = Path(vault) if vault else get_default_vault_path()
    try:
        set_entry(vault_path, source_key, target_key)
        click.echo(f"Mapped {source_key!r} -> {target_key!r}")
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@map_group.command("remove")
@click.argument("source_key")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_map_remove(source_key: str, vault: str | None) -> None:
    """Remove a mapping for SOURCE_KEY."""
    vault_path = Path(vault) if vault else get_default_vault_path()
    removed = remove_entry(vault_path, source_key)
    if removed:
        click.echo(f"Removed mapping for {source_key!r}")
    else:
        click.echo(f"No mapping found for {source_key!r}")


@map_group.command("list")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_map_list(vault: str | None) -> None:
    """List all current import-map entries."""
    vault_path = Path(vault) if vault else get_default_vault_path()
    mapping = load_map(vault_path)
    if not mapping:
        click.echo("No import-map entries.")
        return
    width = max(len(k) for k in mapping)
    for src, tgt in sorted(mapping.items()):
        click.echo(f"  {src:<{width}}  ->  {tgt}")
