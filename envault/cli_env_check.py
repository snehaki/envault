"""CLI commands for checking vault completeness against .env.example."""
from __future__ import annotations

from pathlib import Path

import click

from envault.env_check import check_vault
from envault.vault import get_default_vault_path, load_vault


@click.group("check")
def check_group() -> None:
    """Check vault keys against a .env.example reference file."""


@check_group.command("run")
@click.argument("example", default=".env.example", metavar="EXAMPLE_FILE")
@click.option(
    "--vault",
    "vault_path",
    default=None,
    help="Path to vault file (default: .envault.json).",
)
@click.option(
    "--ignore-extra",
    is_flag=True,
    default=False,
    help="Do not report keys in the vault that are absent from EXAMPLE_FILE.",
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Exit with code 1 if any discrepancies are found.",
)
def cmd_check_run(
    example: str,
    vault_path: str | None,
    ignore_extra: bool,
    strict: bool,
) -> None:
    """Compare vault keys with EXAMPLE_FILE (default: .env.example)."""
    example_file = Path(example)
    if not example_file.exists():
        raise click.ClickException(f"Example file not found: {example_file}")

    resolved_vault = Path(vault_path) if vault_path else get_default_vault_path()
    if not resolved_vault.exists():
        raise click.ClickException(f"Vault file not found: {resolved_vault}")

    vault = load_vault(resolved_vault)
    result = check_vault(vault, example_file, ignore_extra=ignore_extra)

    if result.ok:
        click.secho("\u2713 " + result.summary(), fg="green")
    else:
        click.secho(result.summary(), fg="yellow")
        if strict:
            raise click.ClickException("vault does not match example file (strict mode)")
