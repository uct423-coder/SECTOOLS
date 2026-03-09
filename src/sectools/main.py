import os
import sys
import datetime
import glob

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from InquirerPy import inquirer
from InquirerPy.separator import Separator

from sectools import (
    nmap_tool, msf_tool, sqlmap_tool, nikto_tool,
    hydra_tool, gobuster_tool, john_tool, hashcat_tool,
    netcat_tool, recon_tool,
)
from sectools.utils import (
    show_tool_status, generate_report, load_targets_with_notes,
    edit_target_notes, TARGETS_FILE, LOGS_DIR,
)
from sectools.cheatsheets import cheatsheet_menu
from sectools.diff_scans import diff_scans
from sectools.scheduler import schedule_scan, view_scheduled
from sectools.plugins import plugins_menu
from sectools.dashboard import show_dashboard
from sectools.config import config_menu, load_config, save_config
from sectools import (
    hash_id, revshell, encoding, port_ref,
    subnet_calc, passgen, http_probe,
    scan_history, wordlist_mgr, target_groups,
    scan_profiles, auto_installer,
)
from sectools import osint, screenshot, cred_manager, scope, sessions

console = Console()

# All available tool menu items (label -> handler)
ALL_TOOL_ITEMS = [
    # Recon
    ("Recon", "Recon Autopilot — Auto-scan a target", recon_tool.run),
    ("Recon", "Nmap — Network Scanner", nmap_tool.run),
    ("Recon", "Nikto — Web Server Scanner", nikto_tool.run),
    ("Recon", "Gobuster — Directory & DNS Brute Force", gobuster_tool.run),
    ("Recon", "OSINT — Subdomain & Recon", osint.run),
    # Exploitation
    ("Exploitation", "Metasploit — Exploitation Framework", msf_tool.run),
    ("Exploitation", "SQLMap — SQL Injection Tester", sqlmap_tool.run),
    ("Exploitation", "Hydra — Brute Force", hydra_tool.run),
    # Password Cracking
    ("Password Cracking", "John the Ripper — Password Cracker", john_tool.run),
    ("Password Cracking", "Hashcat — GPU Password Cracker", hashcat_tool.run),
    # Networking
    ("Networking", "Netcat — Network Swiss Army Knife", netcat_tool.run),
    ("Networking", "HTTP Probe — Quick URL Scanner", http_probe.run),
    ("Networking", "Port Reference — Common Ports Lookup", port_ref.run),
    ("Networking", "Subnet Calculator — IP/CIDR Math", subnet_calc.run),
    ("Networking", "Screenshot — Capture Web Pages", screenshot.run),
    # Generators
    ("Generators", "Reverse Shell Generator", revshell.run),
    ("Generators", "Password Generator", passgen.run),
    ("Generators", "Encoding / Decoding", encoding.run),
    # Analysis
    ("Analysis", "Hash Identifier", hash_id.run),
    ("Analysis", "Scan History Browser", scan_history.run),
    ("Analysis", "Diff Scans", lambda c: diff_scans(c)),
]

# Labels that are handled specially (not simple handler calls)
SPECIAL_LABELS = {
    "View Saved Targets", "Edit Target Notes", "Target Groups",
    "Scan Profiles", "Wordlist Manager", "Schedule a Scan",
    "View Scheduled Scans", "Scope Manager", "Credential Manager",
    "Sessions", "Tool Status — Check installed tools",
    "Install Missing Tools", "Generate Report", "Cheat Sheets",
    "Settings", "Plugins", "Manage Favorites", "Clear Screen", "Exit",
}

HANDLERS = {item[1]: item[2] for item in ALL_TOOL_ITEMS}


def _build_menu_choices() -> list:
    """Build menu choices dynamically, prepending favorites if any."""
    config = load_config()
    favorites = config.get("favorites", [])
    theme = config.get("theme_color", "cyan")

    choices = []

    # Favorites section
    if favorites:
        choices.append(Separator("── Favorites ──"))
        for fav in favorites:
            choices.append(fav)

    # Sections
    sections = [
        ("Recon", []),
        ("Exploitation", []),
        ("Password Cracking", []),
        ("Networking", []),
        ("Generators", []),
        ("Analysis", []),
    ]
    section_map = {s[0]: s[1] for s in sections}
    for cat, label, _ in ALL_TOOL_ITEMS:
        section_map[cat].append(label)

    for section_name, items in sections:
        choices.append(Separator(f"── {section_name} ──"))
        choices.extend(items)

    choices.append(Separator("── Management ──"))
    choices.extend([
        "View Saved Targets",
        "Edit Target Notes",
        "Target Groups",
        "Scan Profiles",
        "Wordlist Manager",
        "Schedule a Scan",
        "View Scheduled Scans",
        "Scope Manager",
        "Credential Manager",
        "Sessions",
    ])

    choices.append(Separator("── Other ──"))
    choices.extend([
        "Tool Status — Check installed tools",
        "Install Missing Tools",
        "Generate Report",
        "Cheat Sheets",
        "Settings",
        "Plugins",
        "Manage Favorites",
        "Clear Screen",
        "Exit",
    ])

    return choices


def _auto_cleanup(console: Console):
    """Delete log files older than log_retention_days."""
    config = load_config()
    retention_days = config.get("log_retention_days", 30)

    if not LOGS_DIR.exists():
        return

    cutoff = datetime.datetime.now() - datetime.timedelta(days=retention_days)
    deleted = 0
    for log_file in LOGS_DIR.glob("*.log"):
        mtime = datetime.datetime.fromtimestamp(log_file.stat().st_mtime)
        if mtime < cutoff:
            log_file.unlink()
            deleted += 1

    if deleted:
        console.print(f"[dim]Auto-cleanup: deleted {deleted} log(s) older than {retention_days} days.[/dim]")


def _manage_favorites(console: Console):
    """Toggle tools as favorites."""
    config = load_config()
    favorites = config.get("favorites", [])

    # All tool labels
    all_labels = [item[1] for item in ALL_TOOL_ITEMS]

    choices = []
    for label in all_labels:
        star = "★ " if label in favorites else "  "
        choices.append(f"{star}{label}")
    choices.append("Done")

    while True:
        choice = inquirer.select(
            message="Toggle favorites (★ = favorited):",
            choices=choices,
            pointer="❯",
        ).execute()

        if choice == "Done":
            break

        # Toggle
        label = choice.lstrip("★ ").strip()
        if label in favorites:
            favorites.remove(label)
            console.print(f"[yellow]Removed {label} from favorites.[/yellow]")
        else:
            favorites.append(label)
            console.print(f"[green]Added {label} to favorites.[/green]")

        # Rebuild choices
        choices = []
        for l in all_labels:
            star = "★ " if l in favorites else "  "
            choices.append(f"{star}{l}")
        choices.append("Done")

    config["favorites"] = favorites
    save_config(config)


def view_targets(console: Console):
    config = load_config()
    theme = config.get("theme_color", "cyan")
    entries = load_targets_with_notes()
    if not entries:
        console.print("[yellow]No saved targets yet.[/yellow]")
        return
    console.rule(f"[bold {theme}]Saved Targets[/bold {theme}]")
    for i, e in enumerate(entries, 1):
        note = f" [dim]— {e['notes']}[/dim]" if e.get("notes") else ""
        group = f" [magenta][{e.get('group', '')}][/magenta]" if e.get("group") else ""
        console.print(f"  [{theme}]{i}.[/{theme}] {e['target']}{group}{note}")
    console.print(f"\n[dim]Stored in {TARGETS_FILE}[/dim]")


def main():
    os.system("clear" if os.name != "nt" else "cls")
    _auto_cleanup(console)
    show_dashboard(console)

    while True:
        menu_choices = _build_menu_choices()
        try:
            choice = inquirer.select(
                message="Select a tool:",
                choices=menu_choices,
                pointer="❯",
            ).execute()
        except (KeyboardInterrupt, EOFError):
            break

        if choice == "Exit":
            console.print("[bold green]Goodbye![/bold green]")
            break
        elif choice == "Tool Status — Check installed tools":
            show_tool_status(console)
        elif choice == "View Saved Targets":
            view_targets(console)
        elif choice == "Edit Target Notes":
            edit_target_notes(console)
        elif choice == "Generate Report":
            generate_report(console)
        elif choice == "Target Groups":
            target_groups.run(console)
        elif choice == "Scan Profiles":
            scan_profiles.run(console)
        elif choice == "Wordlist Manager":
            wordlist_mgr.run(console)
        elif choice == "Schedule a Scan":
            schedule_scan(console)
        elif choice == "View Scheduled Scans":
            view_scheduled(console)
        elif choice == "Scope Manager":
            scope.run(console)
        elif choice == "Credential Manager":
            cred_manager.run(console)
        elif choice == "Sessions":
            sessions.run(console)
        elif choice == "Install Missing Tools":
            auto_installer.run(console)
        elif choice == "Cheat Sheets":
            cheatsheet_menu(console)
        elif choice == "Settings":
            config_menu(console)
        elif choice == "Plugins":
            plugins_menu(console)
        elif choice == "Manage Favorites":
            _manage_favorites(console)
        elif choice == "Clear Screen":
            os.system("clear" if os.name != "nt" else "cls")
            show_dashboard(console)
            continue
        elif choice in HANDLERS:
            try:
                HANDLERS[choice](console)
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Returning to menu.[/yellow]")
            except FileNotFoundError as e:
                tool_name = e.filename or "unknown"
                console.print(f"\n[red]{tool_name} is not installed.[/red]")
                console.print(f"[yellow]Install it with: brew install {tool_name}[/yellow]")

        console.print()


if __name__ == "__main__":
    main()
