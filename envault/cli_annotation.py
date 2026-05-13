"""CLI commands for managing per-key annotations."""

from __future__ import annotations

import click

from envault.annotation import (
    get_annotation,
    list_annotations,
    remove_annotation,
    set_annotation,
)


@click.group("annotation")
def annotation_group() -> None:
    """Manage freeform annotations (notes) for vault keys."""


@annotation_group.command("set")
@click.argument("key")
@click.argument("text")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
def cmd_annotation_set(key: str, text: str, vault_path: str) -> None:
    """Attach an annotation TEXT to KEY."""
    set_annotation(vault_path, key, text)
    click.echo(f"Annotation set for '{key}'.")


@annotation_group.command("remove")
@click.argument("key")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
def cmd_annotation_remove(key: str, vault_path: str) -> None:
    """Remove the annotation for KEY."""
    removed = remove_annotation(vault_path, key)
    if removed:
        click.echo(f"Annotation removed for '{key}'.")
    else:
        click.echo(f"No annotation found for '{key}'.")


@annotation_group.command("show")
@click.argument("key")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
def cmd_annotation_show(key: str, vault_path: str) -> None:
    """Show the annotation for KEY."""
    text = get_annotation(vault_path, key)
    if text is None:
        click.echo(f"No annotation set for '{key}'.")
    else:
        click.echo(text)


@annotation_group.command("list")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
def cmd_annotation_list(vault_path: str) -> None:
    """List all annotated keys."""
    annotations = list_annotations(vault_path)
    if not annotations:
        click.echo("No annotations defined.")
        return
    for key, text in annotations.items():
        click.echo(f"{key}: {text}")
