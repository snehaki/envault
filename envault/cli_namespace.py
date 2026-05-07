"""CLI commands for namespace management."""
from __future__ import annotations

import click

from envault.namespace import (
    set_namespace,
    remove_namespace,
    keys_in_namespace,
    list_namespaces,
    load_namespaces,
)
from envault.vault import get_default_vault_path


@click.group("namespace", help="Group vault keys into logical namespaces.")
def namespace_group() -> None:
    pass


@namespace_group.command("set")
@click.argument("key")
@click.argument("namespace")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_namespace_set(key: str, namespace: str, vault: str | None) -> None:
    """Assign KEY to NAMESPACE."""
    vault_path = vault or get_default_vault_path()
    set_namespace(vault_path, key, namespace)
    click.echo(f"Key '{key}' assigned to namespace '{namespace}'.")


@namespace_group.command("remove")
@click.argument("key")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_namespace_remove(key: str, vault: str | None) -> None:
    """Remove namespace assignment for KEY."""
    vault_path = vault or get_default_vault_path()
    removed = remove_namespace(vault_path, key)
    if removed:
        click.echo(f"Namespace assignment for '{key}' removed.")
    else:
        click.echo(f"Key '{key}' had no namespace assignment.", err=True)
        raise SystemExit(1)


@namespace_group.command("list")
@click.option("--namespace", "ns", default=None, help="Filter by namespace label.")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_namespace_list(ns: str | None, vault: str | None) -> None:
    """List namespace assignments, optionally filtered by NAMESPACE."""
    vault_path = vault or get_default_vault_path()
    if ns:
        keys = keys_in_namespace(vault_path, ns)
        if not keys:
            click.echo(f"No keys in namespace '{ns}'.")
        else:
            for key in keys:
                click.echo(f"{ns}  {key}")
    else:
        mapping = load_namespaces(vault_path)
        if not mapping:
            click.echo("No namespace assignments defined.")
        else:
            for key in sorted(mapping):
                click.echo(f"{mapping[key]}  {key}")


@namespace_group.command("namespaces")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_namespace_namespaces(vault: str | None) -> None:
    """List all namespace labels in use."""
    vault_path = vault or get_default_vault_path()
    labels = list_namespaces(vault_path)
    if not labels:
        click.echo("No namespaces defined.")
    else:
        for label in labels:
            click.echo(label)
