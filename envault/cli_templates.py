"""CLI commands for managing vault key templates."""

from __future__ import annotations

import click

from envault.vault import load_vault, get_default_vault_path
from envault.templates import (
    create_template,
    delete_template,
    list_templates,
    load_templates,
    apply_template,
)


@click.group(name="template")
def template_group() -> None:
    """Manage named key templates."""


@template_group.command("save")
@click.argument("name")
@click.argument("keys", nargs=-1, required=True)
@click.option("--vault", "vault_path", default=None, help="Path to vault file.")
def cmd_template_save(name: str, keys: tuple[str, ...], vault_path: str | None) -> None:
    """Save a named template with the specified KEYS."""
    path = get_default_vault_path() if vault_path is None else vault_path
    try:
        create_template(path, name, list(keys))
        click.echo(f"Template '{name}' saved with keys: {', '.join(sorted(set(keys)))}")
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@template_group.command("list")
@click.option("--vault", "vault_path", default=None, help="Path to vault file.")
def cmd_template_list(vault_path: str | None) -> None:
    """List all saved templates."""
    path = get_default_vault_path() if vault_path is None else vault_path
    names = list_templates(path)
    if not names:
        click.echo("No templates saved.")
        return
    templates = load_templates(path)
    for name in names:
        keys_str = ", ".join(templates[name])
        click.echo(f"  {name}: {keys_str}")


@template_group.command("delete")
@click.argument("name")
@click.option("--vault", "vault_path", default=None, help="Path to vault file.")
def cmd_template_delete(name: str, vault_path: str | None) -> None:
    """Delete a named template."""
    path = get_default_vault_path() if vault_path is None else vault_path
    try:
        delete_template(path, name)
        click.echo(f"Template '{name}' deleted.")
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc


@template_group.command("apply")
@click.argument("name")
@click.option("--vault", "vault_path", default=None, help="Path to vault file.")
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase.")
def cmd_template_apply(name: str, vault_path: str | None, passphrase: str) -> None:
    """Show which keys from template NAME are present in the vault."""
    path = get_default_vault_path() if vault_path is None else vault_path
    try:
        vault = load_vault(path)
        present = apply_template(path, name, vault, passphrase=passphrase)
        if not present:
            click.echo(f"No keys from template '{name}' found in vault.")
        else:
            click.echo(f"Keys present for template '{name}':")
            for key in sorted(present):
                click.echo(f"  {key}")
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
