"""CLI commands for key rating/priority management."""
from __future__ import annotations

import click

from envault.rating import (
    get_rating,
    keys_by_rating,
    load_ratings,
    remove_rating,
    set_rating,
    top_keys,
    MAX_RATING,
    MIN_RATING,
)


@click.group("rating")
def rating_group() -> None:
    """Manage key priority ratings."""


@rating_group.command("set")
@click.argument("key")
@click.argument("rating", type=int)
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Vault file path.")
def cmd_rating_set(key: str, rating: int, vault: str) -> None:
    """Set RATING (1-5) for KEY."""
    try:
        set_rating(vault, key, rating)
        click.echo(f"Rating for '{key}' set to {rating}.")
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@rating_group.command("remove")
@click.argument("key")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Vault file path.")
def cmd_rating_remove(key: str, vault: str) -> None:
    """Remove rating for KEY."""
    removed = remove_rating(vault, key)
    if removed:
        click.echo(f"Rating for '{key}' removed.")
    else:
        click.echo(f"No rating found for '{key}'.")


@rating_group.command("show")
@click.argument("key")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Vault file path.")
def cmd_rating_show(key: str, vault: str) -> None:
    """Show rating for KEY."""
    r = get_rating(vault, key)
    if r is None:
        click.echo(f"No rating set for '{key}'.")
    else:
        click.echo(f"{key}: {r}")


@rating_group.command("list")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Vault file path.")
@click.option("--filter", "filter_rating", type=int, default=None,
              help=f"Show only keys with this rating ({MIN_RATING}-{MAX_RATING}).")
def cmd_rating_list(vault: str, filter_rating: int | None) -> None:
    """List all key ratings."""
    if filter_rating is not None:
        keys = keys_by_rating(vault, filter_rating)
        if not keys:
            click.echo(f"No keys with rating {filter_rating}.")
        for k in keys:
            click.echo(f"{k}: {filter_rating}")
        return
    ratings = load_ratings(vault)
    if not ratings:
        click.echo("No ratings configured.")
        return
    for key in sorted(ratings):
        click.echo(f"{key}: {ratings[key]}")


@rating_group.command("top")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Vault file path.")
@click.option("-n", "count", default=5, show_default=True, help="Number of top keys.")
def cmd_rating_top(vault: str, count: int) -> None:
    """Show top-N highest-rated keys."""
    keys = top_keys(vault, count)
    if not keys:
        click.echo("No ratings configured.")
        return
    ratings = load_ratings(vault)
    for k in keys:
        click.echo(f"{k}: {ratings[k]}")
