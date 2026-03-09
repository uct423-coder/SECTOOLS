"""Credential Manager — encrypted credential storage using Fernet."""

import json
import csv
import os
import base64
import getpass
from pathlib import Path

from rich.console import Console
from rich.table import Table
from InquirerPy import inquirer

CREDS_FILE = Path.home() / ".sectools-creds.json"


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a Fernet key from a password using PBKDF2."""
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def _load_store() -> dict | None:
    """Load the raw credential store file."""
    if not CREDS_FILE.exists():
        return None
    try:
        return json.loads(CREDS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _save_store(store: dict):
    CREDS_FILE.write_text(json.dumps(store, indent=2))
    os.chmod(CREDS_FILE, 0o600)


def _unlock(console: Console) -> tuple | None:
    """Prompt for master password, return (fernet, store) or None."""
    from cryptography.fernet import Fernet, InvalidToken

    store = _load_store()
    password = getpass.getpass("Master password: ")

    if store is None:
        # First-time setup
        confirm = getpass.getpass("Confirm master password: ")
        if password != confirm:
            console.print("[red]Passwords don't match.[/red]")
            return None
        salt = os.urandom(16)
        key = _derive_key(password, salt)
        f = Fernet(key)
        verify_token = f.encrypt(b"sectools-verify").decode()
        store = {
            "salt": base64.b64encode(salt).decode(),
            "verify": verify_token,
            "entries": f.encrypt(b"[]").decode(),
        }
        _save_store(store)
        console.print("[green]Credential store created.[/green]")
        return f, store

    # Existing store — verify password
    salt = base64.b64decode(store["salt"])
    key = _derive_key(password, salt)
    f = Fernet(key)
    try:
        f.decrypt(store["verify"].encode())
    except InvalidToken:
        console.print("[red]Wrong master password.[/red]")
        return None
    return f, store


def _get_entries(f, store: dict) -> list[dict]:
    data = f.decrypt(store["entries"].encode())
    return json.loads(data)


def _set_entries(f, store: dict, entries: list[dict]):
    store["entries"] = f.encrypt(json.dumps(entries).encode()).decode()
    _save_store(store)


def _add_cred(console: Console, f, store: dict):
    target = inquirer.text(message="Target:").execute().strip()
    service = inquirer.text(message="Service:").execute().strip()
    username = inquirer.text(message="Username:").execute().strip()
    password = getpass.getpass("Password: ")
    notes = inquirer.text(message="Notes (optional):").execute().strip()

    entries = _get_entries(f, store)
    entries.append({
        "target": target,
        "service": service,
        "username": username,
        "password": password,
        "notes": notes,
    })
    _set_entries(f, store, entries)
    console.print("[green]Credential saved.[/green]")


def _view_creds(console: Console, f, store: dict):
    entries = _get_entries(f, store)
    if not entries:
        console.print("[yellow]No credentials stored.[/yellow]")
        return

    target_filter = inquirer.text(message="Filter by target (blank for all):").execute().strip()

    table = Table(title="Stored Credentials", border_style="dim")
    table.add_column("#", style="dim")
    table.add_column("Target", style="cyan")
    table.add_column("Service")
    table.add_column("Username", style="green")
    table.add_column("Password", style="red")
    table.add_column("Notes", style="dim")

    shown = 0
    for i, e in enumerate(entries, 1):
        if target_filter and target_filter.lower() not in e.get("target", "").lower():
            continue
        shown += 1
        table.add_row(str(i), e["target"], e["service"], e["username"], e["password"], e.get("notes", ""))

    if shown:
        console.print(table)
    else:
        console.print("[yellow]No matching credentials.[/yellow]")


def _search_creds(console: Console, f, store: dict):
    entries = _get_entries(f, store)
    query = inquirer.text(message="Search term:").execute().strip().lower()
    if not query:
        return

    matches = [
        e for e in entries
        if query in e.get("target", "").lower()
        or query in e.get("service", "").lower()
        or query in e.get("username", "").lower()
        or query in e.get("notes", "").lower()
    ]

    if not matches:
        console.print("[yellow]No matches.[/yellow]")
        return

    table = Table(title=f"Search: {query}", border_style="dim")
    table.add_column("Target", style="cyan")
    table.add_column("Service")
    table.add_column("Username", style="green")
    table.add_column("Password", style="red")
    for m in matches:
        table.add_row(m["target"], m["service"], m["username"], m["password"])
    console.print(table)


def _export_creds(console: Console, f, store: dict):
    entries = _get_entries(f, store)
    if not entries:
        console.print("[yellow]No credentials to export.[/yellow]")
        return

    path = inquirer.text(message="Export CSV path:", default="sectools-creds-export.csv").execute().strip()
    if not path:
        return

    with open(path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["target", "service", "username", "password", "notes"])
        writer.writeheader()
        writer.writerows(entries)

    console.print(f"[bold green]Exported {len(entries)} credentials to {path}[/bold green]")
    console.print("[yellow]Warning: This file contains plaintext passwords. Secure or delete it when done.[/yellow]")


def run(console: Console):
    """Credential Manager sub-menu."""
    try:
        from cryptography.fernet import Fernet  # noqa: F401
    except ImportError:
        console.print("[red]cryptography package not installed.[/red]")
        console.print("[yellow]Install it with: pip install cryptography[/yellow]")
        return

    result = _unlock(console)
    if result is None:
        return
    f, store = result

    while True:
        action = inquirer.select(
            message="Credential Manager:",
            choices=["Add Credential", "View Credentials", "Search", "Export (CSV)", "Back"],
            pointer="❯",
        ).execute()

        if action == "Add Credential":
            _add_cred(console, f, store)
        elif action == "View Credentials":
            _view_creds(console, f, store)
        elif action == "Search":
            _search_creds(console, f, store)
        elif action == "Export (CSV)":
            _export_creds(console, f, store)
        else:
            break
