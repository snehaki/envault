"""CLI commands for per-key PIN protection."""
from __future__ import annotations

import click
from envault.cli import _prompt_passphrase
from envault.vault import get_default_vault_path
from envault import pin as pin_mod


@click.group("pin")
def pin_group() -> None:
    """Manage per-key PIN protection."""


@pin_group.command("set")
@click.argument("key")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_pin_set(key: str, vault: str | None) -> None:
    """Set a PIN on KEY (prompts for PIN twice)."""
    vault_path = vault or get_default_vault_path()
    pin_val = click.prompt("Enter new PIN", hide_input=True)
    confirm = click.prompt("Confirm PIN", hide_input=True)
    if pin_val != confirm:
        raise click.ClickException("PINs do not match.")
    try:
        pin_mod.set_pin(vault_path, key, pin_val)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"PIN set for '{key}'.")


@pin_group.command("remove")
@click.argument("key")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_pin_remove(key: str, vault: str | None) -> None:
    """Remove PIN protection from KEY."""
    vault_path = vault or get_default_vault_path()
    removed = pin_mod.remove_pin(vault_path, key)
    if removed:
        click.echo(f"PIN removed from '{key}'.")
    else:
        click.echo(f"No PIN was set for '{key}'.")


@pin_group.command("list")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_pin_list(vault: str | None) -> None:
    """List all keys that have a PIN set."""
    vault_path = vault or get_default_vault_path()
    keys = pin_mod.pinned_keys(vault_path)
    if not keys:
        click.echo("No keys are PIN-protected.")
    else:
        for k in keys:
            click.echo(f"  {k}")


@pin_group.command("verify")
@click.argument("key")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_pin_verify(key: str, vault: str | None) -> None:
    """Interactively verify the PIN for KEY."""
    vault_path = vault or get_default_vault_path()
    if not pin_mod.is_pinned(vault_path, key):
        click.echo(f"'{key}' has no PIN set.")
        return
    pin_val = click.prompt("Enter PIN", hide_input=True)
    if pin_mod.verify_pin(vault_path, key, pin_val):
        click.echo("PIN correct.")
    else:
        raise click.ClickException("Incorrect PIN.")
