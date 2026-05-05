"""CLI commands for vault bundle share/receive (share sub-group)."""

from __future__ import annotations

import click

from envault.share import (
    export_bundle,
    import_bundle,
    read_bundle_file,
    write_bundle_file,
)
from envault.vault import get_default_vault_path, load_vault, save_vault


@click.group("share")
def share_group() -> None:
    """Commands for sharing vault secrets securely."""


@share_group.command("export")
@click.option("--vault", "vault_path", default=None, help="Path to vault file.")
@click.option("--out", "out_path", required=True, help="Output bundle file path.")
def cmd_share_export(vault_path: str | None, out_path: str) -> None:
    """Export vault as an encrypted bundle for sharing."""
    vault_path = vault_path or get_default_vault_path()
    src_pass = click.prompt("Vault passphrase", hide_input=True)
    bundle_pass = click.prompt("Bundle passphrase (for recipient)", hide_input=True)
    bundle_pass_confirm = click.prompt("Confirm bundle passphrase", hide_input=True)

    if bundle_pass != bundle_pass_confirm:
        raise click.ClickException("Bundle passphrases do not match.")

    vault = load_vault(vault_path)
    if not vault:
        raise click.ClickException("Vault is empty — nothing to export.")

    bundle = export_bundle(vault, src_pass, bundle_pass)
    write_bundle_file(bundle, out_path)
    click.echo(f"Bundle written to {out_path} ({len(vault)} keys).")


@share_group.command("import")
@click.argument("bundle_file")
@click.option("--vault", "vault_path", default=None, help="Path to destination vault.")
@click.option("--merge", is_flag=True, default=False, help="Merge into existing vault.")
def cmd_share_import(
    bundle_file: str,
    vault_path: str | None,
    merge: bool,
) -> None:
    """Import an encrypted bundle into the local vault."""
    vault_path = vault_path or get_default_vault_path()
    bundle_pass = click.prompt("Bundle passphrase", hide_input=True)
    dest_pass = click.prompt("New vault passphrase", hide_input=True)

    bundle = read_bundle_file(bundle_file)
    imported = import_bundle(bundle, bundle_pass, dest_pass)

    if merge:
        existing = load_vault(vault_path)
        existing.update(imported)
        save_vault(vault_path, existing)
        click.echo(f"Merged {len(imported)} keys into {vault_path}.")
    else:
        save_vault(vault_path, imported)
        click.echo(f"Imported {len(imported)} keys into {vault_path}.")
