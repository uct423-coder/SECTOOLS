"""Scope Checker — manage and enforce engagement scope."""

import json
import ipaddress
from pathlib import Path

from rich.console import Console
from rich.table import Table
from InquirerPy import inquirer

SCOPE_FILE = Path.home() / ".sectools-scope.json"


def _load_scope() -> dict:
    if SCOPE_FILE.exists():
        try:
            return json.loads(SCOPE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"cidrs": [], "domains": []}


def _save_scope(scope: dict):
    SCOPE_FILE.write_text(json.dumps(scope, indent=2))


def is_in_scope(target: str) -> bool | None:
    """Check if a target is in scope. Returns None if no scope defined."""
    scope = _load_scope()
    if not scope["cidrs"] and not scope["domains"]:
        return None  # No scope defined

    # Check domain suffix match
    for domain in scope["domains"]:
        if target == domain or target.endswith(f".{domain}"):
            return True

    # Check CIDR match
    try:
        addr = ipaddress.ip_address(target)
        for cidr in scope["cidrs"]:
            if addr in ipaddress.ip_network(cidr, strict=False):
                return True
    except ValueError:
        pass  # Not an IP address

    return False


def _view_scope(console: Console):
    scope = _load_scope()
    if not scope["cidrs"] and not scope["domains"]:
        console.print("[yellow]No scope defined.[/yellow]")
        return

    table = Table(title="Current Scope", border_style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Value")
    for cidr in scope["cidrs"]:
        table.add_row("CIDR", cidr)
    for domain in scope["domains"]:
        table.add_row("Domain", domain)
    console.print(table)


def _add_cidr(console: Console):
    cidr = inquirer.text(message="CIDR (e.g. 10.0.0.0/24):").execute().strip()
    if not cidr:
        return
    try:
        ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        console.print("[red]Invalid CIDR.[/red]")
        return
    scope = _load_scope()
    if cidr not in scope["cidrs"]:
        scope["cidrs"].append(cidr)
        _save_scope(scope)
    console.print(f"[green]✔ Added {cidr} to scope.[/green]")


def _add_domain(console: Console):
    domain = inquirer.text(message="Domain (e.g. example.com):").execute().strip()
    if not domain:
        return
    scope = _load_scope()
    if domain not in scope["domains"]:
        scope["domains"].append(domain)
        _save_scope(scope)
    console.print(f"[green]✔ Added {domain} to scope.[/green]")


def _clear_scope(console: Console):
    confirm = inquirer.confirm(message="Clear all scope entries?", default=False).execute()
    if confirm:
        _save_scope({"cidrs": [], "domains": []})
        console.print("[green]✔ Scope cleared.[/green]")


def run(console: Console):
    """Scope Manager sub-menu."""
    while True:
        action = inquirer.select(
            message="Scope Manager:",
            choices=["View Scope", "Add CIDR", "Add Domain", "Clear Scope", "Back"],
            pointer="❯",
        ).execute()

        if action == "View Scope":
            _view_scope(console)
        elif action == "Add CIDR":
            _add_cidr(console)
        elif action == "Add Domain":
            _add_domain(console)
        elif action == "Clear Scope":
            _clear_scope(console)
        else:
            break
