"""Scan Profiles — save and replay tool configurations."""

from __future__ import annotations

import json
from pathlib import Path

from InquirerPy import inquirer
from rich.console import Console
from rich.table import Table

from sectools.utils import ask_target, check_installed, run_logged

PROFILES_FILE = Path.home() / ".sectools-profiles.json"

TOOL_CHOICES = [
    "nmap",
    "nikto",
    "gobuster",
    "sqlmap",
    "hydra",
    "john",
    "hashcat",
]


def _load_profiles() -> list[dict]:
    if not PROFILES_FILE.exists():
        return []
    raw = PROFILES_FILE.read_text().strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _save_profiles(profiles: list[dict]) -> None:
    PROFILES_FILE.write_text(json.dumps(profiles, indent=2))


def _view_profiles(console: Console) -> None:
    profiles = _load_profiles()
    if not profiles:
        console.print("[yellow]No profiles saved.[/yellow]")
        return

    table = Table(title="Scan Profiles", border_style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Tool", style="green")
    table.add_column("Flags", style="white")
    table.add_column("Description", style="dim")

    for p in profiles:
        table.add_row(
            p["name"],
            p["tool"],
            " ".join(p.get("flags", [])),
            p.get("description", ""),
        )

    console.print(table)
    console.print()


def _create_profile(console: Console) -> None:
    tool = inquirer.select(
        message="Tool:",
        choices=TOOL_CHOICES,
        pointer="❯",
    ).execute()

    name = inquirer.text(message="Profile name:").execute().strip()
    if not name:
        console.print("[red]No name provided.[/red]")
        return

    flags_raw = inquirer.text(message="Flags (space-separated):").execute().strip()
    flags = flags_raw.split() if flags_raw else []

    description = inquirer.text(message="Description (optional):").execute().strip()

    profiles = _load_profiles()
    profiles.append({
        "name": name,
        "tool": tool,
        "flags": flags,
        "description": description,
    })
    _save_profiles(profiles)
    console.print(f"[green]Profile '{name}' saved.[/green]")


def _run_profile(console: Console) -> None:
    profiles = _load_profiles()
    if not profiles:
        console.print("[yellow]No profiles saved.[/yellow]")
        return

    choices = [f"{p['name']}  ({p['tool']} {' '.join(p.get('flags', []))})" for p in profiles]
    picked = inquirer.select(message="Select profile:", choices=choices, pointer="❯").execute()
    idx = choices.index(picked)
    profile = profiles[idx]

    binary = profile["tool"]
    if not check_installed(binary):
        console.print(f"[red]{binary} is not installed.[/red]")
        return

    target = ask_target(console)
    if not target:
        return

    cmd = [binary] + profile.get("flags", []) + [target]
    run_logged(cmd, console, f"{binary}_profile")


def _delete_profile(console: Console) -> None:
    profiles = _load_profiles()
    if not profiles:
        console.print("[yellow]No profiles saved.[/yellow]")
        return

    choices = [p["name"] for p in profiles]
    picked = inquirer.select(message="Delete profile:", choices=choices, pointer="❯").execute()
    idx = choices.index(picked)

    removed = profiles.pop(idx)
    _save_profiles(profiles)
    console.print(f"[green]Profile '{removed['name']}' deleted.[/green]")


def run(console: Console) -> None:
    """Entry point for the Scan Profiles module."""
    while True:
        action = inquirer.select(
            message="Scan Profiles:",
            choices=[
                "View Profiles",
                "Create Profile",
                "Run Profile",
                "Delete Profile",
                "Back",
            ],
            pointer="❯",
        ).execute()

        if action == "View Profiles":
            _view_profiles(console)
        elif action == "Create Profile":
            _create_profile(console)
        elif action == "Run Profile":
            _run_profile(console)
        elif action == "Delete Profile":
            _delete_profile(console)
        else:
            break
