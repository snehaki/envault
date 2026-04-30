"""CLI entry point for envault."""

import sys
import getpass
from pathlib import Path

import click

from envault.vault import load_vault, save_vault, get_default_vault_path


def _prompt_passphrase(confirm: bool = False) -> str:
    passphrase = getpass.getpass("Passphrase: ")
    if confirm:
        second = getpass.getpass("Confirm passphrase: ")
        if passphrase != second:
            click.echo("Error: passphrases do not match.", err=True)
            sys.exit(1)
    return passphrase


@click.group()
def cli() -> None:
    """envault — manage and encrypt per-project .env files."""


@cli.command("set")
@click.argument("key")
@click.argument("value")
def cmd_set(key: str, value: str) -> None:
    """Set a secret KEY to VALUE in the vault."""
    passphrase = _prompt_passphrase(confirm=False)
    vault_path = get_default_vault_path()
    data = load_vault(vault_path, passphrase)
    data[key] = value
    save_vault(vault_path, passphrase, data)
    click.echo(f"Set '{key}' in {vault_path}")


@cli.command("get")
@click.argument("key")
def cmd_get(key: str) -> None:
    """Get the value of KEY from the vault."""
    passphrase = _prompt_passphrase(confirm=False)
    vault_path = get_default_vault_path()
    data = load_vault(vault_path, passphrase)
    if key not in data:
        click.echo(f"Key '{key}' not found.", err=True)
        sys.exit(1)
    click.echo(data[key])


@cli.command("list")
def cmd_list() -> None:
    """List all keys stored in the vault."""
    passphrase = _prompt_passphrase(confirm=False)
    vault_path = get_default_vault_path()
    data = load_vault(vault_path, passphrase)
    if not data:
        click.echo("Vault is empty.")
        return
    for k in sorted(data):
        click.echo(k)


if __name__ == "__main__":
    cli()
