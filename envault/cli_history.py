"""CLI commands for per-key value history."""
from __future__ import annotations

import click

from envault.crypto import decrypt
from envault.history import get_history, clear_history
from envault.vault import get_default_vault_path
from envault.cli import _prompt_passphrase


@click.group("history")
def history_group() -> None:
    """View or manage per-key value history."""


@history_group.command("show")
@click.argument("key")
@click.option("--vault", default=None, help="Path to vault file.")
@click.option("--decrypt-values", is_flag=True, default=False, help="Decrypt and show plaintext values.")
def cmd_history_show(key: str, vault: str | None, decrypt_values: bool) -> None:
    """Show stored history for KEY."""
    vault_path = get_default_vault_path() if vault is None else __import__("pathlib").Path(vault)
    entries = get_history(vault_path, key)
    if not entries:
        click.echo(f"No history found for '{key}'.")
        return

    passphrase = _prompt_passphrase() if decrypt_values else None

    click.echo(f"History for '{key}' ({len(entries)} entries):")
    for idx, entry in enumerate(entries, 1):
        ts = entry.get("timestamp", "unknown")
        if decrypt_values and passphrase:
            try:
                plaintext = decrypt(entry["ciphertext"], passphrase)
                value_display = plaintext
            except Exception:
                value_display = "<decryption failed>"
        else:
            value_display = entry["ciphertext"][:20] + "…"
        click.echo(f"  [{idx:>2}] {ts}  {value_display}")


@history_group.command("clear")
@click.argument("key")
@click.option("--vault", default=None, help="Path to vault file.")
@click.confirmation_option(prompt="Clear all history for this key?")
def cmd_history_clear(key: str, vault: str | None) -> None:
    """Clear stored history for KEY."""
    vault_path = get_default_vault_path() if vault is None else __import__("pathlib").Path(vault)
    clear_history(vault_path, key)
    click.echo(f"History cleared for '{key}'.")
