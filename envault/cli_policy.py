"""CLI commands for key policy management."""
from __future__ import annotations

import click

from envault.policy import (
    get_policy,
    load_policies,
    remove_policy,
    set_policy,
    validate_value,
)
from envault.vault import get_default_vault_path, load_vault
from envault.crypto import decrypt


@click.group("policy")
def policy_group() -> None:
    """Manage per-key validation policies."""


@policy_group.command("set")
@click.argument("key")
@click.argument("rule")
@click.argument("value")
@click.option("--vault", default=None, help="Path to vault file.")
def cmd_policy_set(key: str, rule: str, value: str, vault: str | None) -> None:
    """Set a policy RULE for KEY (e.g. min_length 8)."""
    vault_path = vault or get_default_vault_path()
    # coerce numeric values
    coerced: object = value
    if value.isdigit():
        coerced = int(value)
    elif value.lower() in {"true", "false"}:
        coerced = value.lower() == "true"
    set_policy(vault_path, key, rule, coerced)
    click.echo(f"Policy '{rule}={coerced}' set for key '{key}'.")


@policy_group.command("remove")
@click.argument("key")
@click.option("--vault", default=None)
def cmd_policy_remove(key: str, vault: str | None) -> None:
    """Remove all policies for KEY."""
    vault_path = vault or get_default_vault_path()
    removed = remove_policy(vault_path, key)
    if removed:
        click.echo(f"Policies removed for '{key}'.")
    else:
        click.echo(f"No policies found for '{key}'.")


@policy_group.command("list")
@click.option("--vault", default=None)
def cmd_policy_list(vault: str | None) -> None:
    """List all defined policies."""
    vault_path = vault or get_default_vault_path()
    policies = load_policies(vault_path)
    if not policies:
        click.echo("No policies defined.")
        return
    for key, rules in sorted(policies.items()):
        rule_str = ", ".join(f"{r}={v}" for r, v in sorted(rules.items()))
        click.echo(f"  {key}: {rule_str}")


@policy_group.command("check")
@click.option("--vault", default=None)
@click.option("--passphrase", prompt=True, hide_input=True)
def cmd_policy_check(vault: str | None, passphrase: str) -> None:
    """Validate all vault values against their policies."""
    vault_path = vault or get_default_vault_path()
    vault_data = load_vault(vault_path)
    policies = load_policies(vault_path)
    all_issues: list[str] = []
    for key, rules in policies.items():
        encrypted = vault_data.get("secrets", {}).get(key)
        if encrypted is None:
            if rules.get("required"):
                all_issues.append(f"{key}: key is required but not present in vault")
            continue
        value = decrypt(encrypted, passphrase)
        all_issues.extend(validate_value(key, value, rules))
    if all_issues:
        for issue in all_issues:
            click.echo(f"  FAIL  {issue}")
        raise SystemExit(1)
    click.echo("All policy checks passed.")
