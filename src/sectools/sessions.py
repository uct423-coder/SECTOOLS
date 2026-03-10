"""Session System — isolate targets and logs per engagement."""

import json
import shutil
from pathlib import Path

from rich.console import Console
from rich.table import Table
from InquirerPy import inquirer

import sectools.utils as utils

SESSIONS_DIR = Path.home() / ".sectools-sessions"

_active_session: str | None = None


def get_active_session() -> str | None:
    """Return the name of the active session, or None."""
    return _active_session


def activate_session(name: str):
    """Point utils.LOGS_DIR and utils.TARGETS_FILE into the session directory."""
    global _active_session
    session_dir = SESSIONS_DIR / name
    session_dir.mkdir(parents=True, exist_ok=True)

    logs_dir = session_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    targets_file = session_dir / "targets.json"
    if not targets_file.exists():
        targets_file.write_text("[]")

    session_meta = session_dir / "session.json"
    if not session_meta.exists():
        import datetime
        session_meta.write_text(json.dumps({
            "name": name,
            "created": datetime.datetime.now().isoformat(),
        }, indent=2))

    utils.LOGS_DIR = logs_dir
    utils.TARGETS_FILE = targets_file
    _active_session = name


def deactivate_session():
    """Reset utils paths to defaults."""
    global _active_session
    utils.LOGS_DIR = Path.home() / "sectools-logs"
    utils.TARGETS_FILE = Path.home() / ".sectools-targets"
    _active_session = None


def _list_sessions() -> list[str]:
    if not SESSIONS_DIR.exists():
        return []
    return sorted(d.name for d in SESSIONS_DIR.iterdir() if d.is_dir())


def _new_session(console: Console):
    name = inquirer.text(message="Session name:").execute().strip()
    if not name:
        console.print("[red]No name provided.[/red]")
        return
    if (SESSIONS_DIR / name).exists():
        console.print("[yellow]Session already exists. Switching to it.[/yellow]")
    activate_session(name)
    console.print(f"[green]✔ Session '{name}' activated.[/green]")


def _switch_session(console: Console):
    sessions = _list_sessions()
    if not sessions:
        console.print("[yellow]No sessions found.[/yellow]")
        return
    name = inquirer.select(message="Switch to:", choices=sessions, pointer="❯").execute()
    activate_session(name)
    console.print(f"[green]✔ Switched to session '{name}'.[/green]")


def _end_session(console: Console):
    if not _active_session:
        console.print("[yellow]No active session.[/yellow]")
        return
    name = _active_session
    deactivate_session()
    console.print(f"[green]✔ Session '{name}' ended. Back to default workspace.[/green]")


def _show_sessions(console: Console):
    sessions = _list_sessions()
    if not sessions:
        console.print("[yellow]No sessions.[/yellow]")
        return
    table = Table(title="Sessions", border_style="dim", show_lines=False)
    table.add_column("", width=3, justify="center")
    table.add_column("Name", style="bold")
    for s in sessions:
        icon = "[green]●[/green]" if s == _active_session else "[dim]○[/dim]"
        table.add_row(icon, s)
    console.print(table)


def run(console: Console):
    """Sessions sub-menu."""
    while True:
        action = inquirer.select(
            message="Sessions:",
            choices=["New Session", "Switch Session", "End Session", "List Sessions", "Back"],
            pointer="❯",
        ).execute()

        if action == "New Session":
            _new_session(console)
        elif action == "Switch Session":
            _switch_session(console)
        elif action == "End Session":
            _end_session(console)
        elif action == "List Sessions":
            _show_sessions(console)
        else:
            break
