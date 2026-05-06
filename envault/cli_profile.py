"""CLI commands for managing vault profiles."""
from __future__ import annotations

import click

from .vault import load_vault, get_default_vault_path
from .profile import (
    create_profile,
    delete_profile,
    get_profile_keys,
    list_profiles,
    profile_keys_from_vault,
)
from .crypto import decrypt


@click.group("profile")
def profile_group() -> None:
    """Manage named key profiles (subsets of vault keys)."""


@profile_group.command("save")
@click.argument("name")
@click.argument("keys", nargs=-1, required=True)
@click.option("--vault", "vault_path", default=None, help="Path to vault file.")
def cmd_profile_save(name: str, keys: tuple, vault_path: str | None) -> None:
    """Save a profile NAME containing the specified KEYS."""
    vault_path = vault_path or get_default_vault_path()
    create_profile(vault_path, name, list(keys))
    click.echo(f"Profile '{name}' saved with {len(keys)} key(s).")


@profile_group.command("list")
@click.option("--vault", "vault_path", default=None, help="Path to vault file.")
def cmd_profile_list(vault_path: str | None) -> None:
    """List all saved profiles."""
    vault_path = vault_path or get_default_vault_path()
    names = list_profiles(vault_path)
    if not names:
        click.echo("No profiles defined.")
        return
    for name in names:
        keys = get_profile_keys(vault_path, name)
        click.echo(f"{name}: {', '.join(keys)}")


@profile_group.command("delete")
@click.argument("name")
@click.option("--vault", "vault_path", default=None, help="Path to vault file.")
def cmd_profile_delete(name: str, vault_path: str | None) -> None:
    """Delete a profile by NAME."""
    vault_path = vault_path or get_default_vault_path()
    try:
        delete_profile(vault_path, name)
        click.echo(f"Profile '{name}' deleted.")
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc


@profile_group.command("show")
@click.argument("name")
@click.option("--decrypt", "do_decrypt", is_flag=True, help="Decrypt and show values.")
@click.option("--passphrase", default=None, hidden=True)
@click.option("--vault", "vault_path", default=None, help="Path to vault file.")
def cmd_profile_show(
    name: str, do_decrypt: bool, passphrase: str | None, vault_path: str | None
) -> None:
    """Show keys (and optionally values) for profile NAME."""
    vault_path = vault_path or get_default_vault_path()
    try:
        vault_data = load_vault(vault_path)
        mapping = profile_keys_from_vault(vault_path, name, vault_data)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc

    if do_decrypt:
        if passphrase is None:
            passphrase = click.prompt("Passphrase", hide_input=True)
        for key, enc_val in mapping.items():
            if enc_val is None:
                click.echo(f"{key}=<not set>")
            else:
                try:
                    value = decrypt(enc_val, passphrase)
                    click.echo(f"{key}={value}")
                except Exception:
                    click.echo(f"{key}=<decryption failed>")
    else:
        for key, enc_val in mapping.items():
            status = "set" if enc_val is not None else "not set"
            click.echo(f"{key} ({status})")
