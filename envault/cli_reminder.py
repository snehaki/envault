"""CLI commands for key-rotation reminders."""

from __future__ import annotations

from pathlib import Path

import click

from envault.reminder import (
    check_reminders,
    load_reminders,
    remove_reminder,
    set_reminder,
)
from envault.vault import get_default_vault_path


@click.group("reminder")
def reminder_group() -> None:
    """Manage key-rotation reminders."""


@reminder_group.command("set")
@click.argument("key")
@click.argument("days", type=int)
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_reminder_set(key: str, days: int, vault: str | None) -> None:
    """Set a rotation reminder for KEY every DAYS days."""
    vault_path = Path(vault) if vault else get_default_vault_path()
    try:
        set_reminder(vault_path, key, days)
        click.echo(f"Reminder set: '{key}' should be rotated every {days} day(s).")
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@reminder_group.command("remove")
@click.argument("key")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_reminder_remove(key: str, vault: str | None) -> None:
    """Remove the rotation reminder for KEY."""
    vault_path = Path(vault) if vault else get_default_vault_path()
    removed = remove_reminder(vault_path, key)
    if removed:
        click.echo(f"Reminder for '{key}' removed.")
    else:
        click.echo(f"No reminder found for '{key}'.")


@reminder_group.command("list")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_reminder_list(vault: str | None) -> None:
    """List all configured reminders."""
    vault_path = Path(vault) if vault else get_default_vault_path()
    data = load_reminders(vault_path)
    if not data:
        click.echo("No reminders configured.")
        return
    for key, entry in sorted(data.items()):
        click.echo(f"  {key}: every {entry['rotate_after_days']} day(s), set at {entry['set_at']}")


@reminder_group.command("check")
@click.option("--warn-days", default=7, show_default=True, help="Warn N days before due.")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_reminder_check(warn_days: int, vault: str | None) -> None:
    """Check for keys due for rotation."""
    vault_path = Path(vault) if vault else get_default_vault_path()
    due = check_reminders(vault_path, warn_days=warn_days)
    if not due:
        click.echo("All keys are up to date.")
        return
    for status in due:
        label = click.style("OVERDUE", fg="red") if status.overdue else click.style("DUE SOON", fg="yellow")
        click.echo(
            f"  [{label}] {status.key}: due {status.due_date.date()} "
            f"({abs(status.days_remaining)} day(s) {'ago' if status.overdue else 'remaining'})"
        )
