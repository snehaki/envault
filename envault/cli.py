"""CLI entry-point for envault."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from envault import audit
from envault.crypto import decrypt, encrypt
from envault.export import export_env, import_env
from envault.vault import get_default_vault_path, load_vault, save_vault


def _prompt_passphrase(confirm: bool = False) -> str:
    passphrase = click.prompt("Passphrase", hide_input=True)
    if confirm:
        click.prompt("Confirm passphrase", hide_input=True, confirmation_prompt=True)
    return passphrase


@click.group()
@click.option("--vault", default=None, help="Path to vault file.")
@click.pass_context
def cli(ctx: click.Context, vault: str | None) -> None:
    """envault — encrypted .env manager."""
    ctx.ensure_object(dict)
    ctx.obj["vault_path"] = Path(vault) if vault else get_default_vault_path()


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def cmd_set(ctx: click.Context, key: str, value: str) -> None:
    """Encrypt and store a secret."""
    vault_path: Path = ctx.obj["vault_path"]
    passphrase = _prompt_passphrase()
    vault = load_vault(vault_path)
    vault[key] = encrypt(value, passphrase)
    save_vault(vault_path, vault)
    audit.record(vault_path, "set", key)
    click.echo(f"✓ '{key}' saved.")


@cli.command("get")
@click.argument("key")
@click.pass_context
def cmd_get(ctx: click.Context, key: str) -> None:
    """Decrypt and print a secret."""
    vault_path: Path = ctx.obj["vault_path"]
    passphrase = _prompt_passphrase()
    vault = load_vault(vault_path)
    if key not in vault:
        click.echo(f"Key '{key}' not found.", err=True)
        sys.exit(1)
    value = decrypt(vault[key], passphrase)
    audit.record(vault_path, "get", key)
    click.echo(value)


@cli.command("list")
@click.pass_context
def cmd_list(ctx: click.Context) -> None:
    """List all stored keys."""
    vault_path: Path = ctx.obj["vault_path"]
    vault = load_vault(vault_path)
    if not vault:
        click.echo("No secrets stored.")
        return
    for key in sorted(vault.keys()):
        click.echo(key)


@cli.command("export")
@click.option("--output", "-o", default=None, help="Write to this file instead of stdout.")
@click.pass_context
def cmd_export(ctx: click.Context, output: str | None) -> None:
    """Export decrypted secrets as a .env file."""
    vault_path: Path = ctx.obj["vault_path"]
    passphrase = _prompt_passphrase()
    out_path = Path(output) if output else None
    content = export_env(vault_path, passphrase, out_path)
    audit.record(vault_path, "export")
    if out_path:
        click.echo(f"✓ Exported to {out_path}")
    else:
        click.echo(content, nl=False)


@cli.command("import")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys.")
@click.pass_context
def cmd_import(ctx: click.Context, env_file: Path, overwrite: bool) -> None:
    """Import secrets from a plain .env file into the vault."""
    vault_path: Path = ctx.obj["vault_path"]
    passphrase = _prompt_passphrase(confirm=True)
    try:
        imported = import_env(vault_path, passphrase, env_file, overwrite=overwrite)
    except ValueError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    audit.record(vault_path, "import")
    click.echo(f"✓ Imported {len(imported)} key(s): {', '.join(imported)}")


@cli.command("log")
@click.pass_context
def cmd_log(ctx: click.Context) -> None:
    """Show the audit log for the current vault."""
    vault_path: Path = ctx.obj["vault_path"]
    entries = audit.read_log(vault_path)
    click.echo(audit.format_log(entries))
