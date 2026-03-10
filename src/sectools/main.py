import os
import sys
import datetime

from rich.console import Console
from rich.panel import Panel
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

# ── Category sub-menus ──────────────────────────────────────────────

CATEGORIES = {
    "Recon & OSINT": [
        ("Recon Autopilot", recon_tool.run),
        ("Nmap — Network Scanner", nmap_tool.run),
        ("Nikto — Web Server Scanner", nikto_tool.run),
        ("Gobuster — Dir & DNS Brute Force", gobuster_tool.run),
        ("OSINT — Subdomain & Recon", osint.run),
    ],
    "Exploitation": [
        ("Metasploit — Framework", msf_tool.run),
        ("SQLMap — SQL Injection", sqlmap_tool.run),
        ("Hydra — Brute Force", hydra_tool.run),
    ],
    "Password Cracking": [
        ("John the Ripper", john_tool.run),
        ("Hashcat — GPU Cracker", hashcat_tool.run),
    ],
    "Networking & Web": [
        ("Netcat — Network Swiss Army Knife", netcat_tool.run),
        ("HTTP Probe — Quick URL Scanner", http_probe.run),
        ("Screenshot — Capture Web Pages", screenshot.run),
        ("Port Reference", port_ref.run),
        ("Subnet Calculator", subnet_calc.run),
    ],
    "Generators": [
        ("Reverse Shell Generator", revshell.run),
        ("Password Generator", passgen.run),
        ("Encoding / Decoding", encoding.run),
    ],
    "Analysis": [
        ("Hash Identifier", hash_id.run),
        ("Scan History Browser", scan_history.run),
        ("Diff Scans", lambda c: diff_scans(c)),
    ],
}

# Flat lookup for favorites
ALL_TOOL_ITEMS = []
HANDLERS = {}
for _cat, _tools in CATEGORIES.items():
    for _label, _handler in _tools:
        ALL_TOOL_ITEMS.append((_cat, _label, _handler))
        HANDLERS[_label] = _handler


def _run_category(console: Console, category: str):
    """Show a sub-menu for a tool category."""
    tools = CATEGORIES[category]
    choices = [t[0] for t in tools] + ["Back"]

    while True:
        choice = inquirer.select(
            message=f"{category}:",
            choices=choices,
            pointer="❯",
        ).execute()

        if choice == "Back":
            return

        handler = dict(tools)[choice]
        try:
            handler(console)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/yellow]")
        except FileNotFoundError as e:
            tool_name = e.filename or "unknown"
            console.print(f"\n[red]{tool_name} is not installed.[/red]")
            console.print(f"[yellow]Install it with: brew install {tool_name}[/yellow]")
        console.print()


def _build_menu_choices() -> list:
    """Build the compact main menu."""
    config = load_config()
    favorites = config.get("favorites", [])

    choices = []

    # Favorites at the top
    if favorites:
        choices.append(Separator("── Favorites ──"))
        for fav in favorites:
            choices.append(fav)

    # Tool categories
    choices.append(Separator("── Tools ──"))
    for cat in CATEGORIES:
        count = len(CATEGORIES[cat])
        choices.append(f"{cat}  ({count})")

    # Other
    choices.append(Separator("──────────"))
    choices.extend([
        "Management",
        "Generate Report",
        "Cheat Sheets",
        "Settings",
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


def _management_submenu(console: Console):
    """Management sub-menu — targets, profiles, scope, sessions, etc."""
    config = load_config()
    theme = config.get("theme_color", "cyan")

    while True:
        choice = inquirer.select(
            message="Management:",
            choices=[
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
                Separator("──────────"),
                "Tool Status",
                "Install Missing Tools",
                "Plugins",
                "Back",
            ],
            pointer="❯",
        ).execute()

        if choice == "Back":
            return
        elif choice == "View Saved Targets":
            entries = load_targets_with_notes()
            if not entries:
                console.print("[yellow]No saved targets yet.[/yellow]")
            else:
                console.rule(f"[bold {theme}]Saved Targets[/bold {theme}]")
                for i, e in enumerate(entries, 1):
                    note = f" [dim]— {e['notes']}[/dim]" if e.get("notes") else ""
                    group = f" [magenta][{e.get('group', '')}][/magenta]" if e.get("group") else ""
                    console.print(f"  [{theme}]{i}.[/{theme}] {e['target']}{group}{note}")
                console.print(f"\n[dim]Stored in {TARGETS_FILE}[/dim]")
        elif choice == "Edit Target Notes":
            edit_target_notes(console)
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
        elif choice == "Tool Status":
            show_tool_status(console)
        elif choice == "Install Missing Tools":
            auto_installer.run(console)
        elif choice == "Plugins":
            plugins_menu(console)
        console.print()


def _manage_favorites(console: Console):
    """Toggle tools as favorites."""
    config = load_config()
    favorites = config.get("favorites", [])
    all_labels = [item[1] for item in ALL_TOOL_ITEMS]

    def _build_choices():
        c = []
        for label in all_labels:
            star = "★ " if label in favorites else "  "
            c.append(f"{star}{label}")
        c.append("Done")
        return c

    while True:
        choice = inquirer.select(
            message="Toggle favorites (★ = favorited):",
            choices=_build_choices(),
            pointer="❯",
        ).execute()

        if choice == "Done":
            break

        label = choice.lstrip("★ ").strip()
        if label in favorites:
            favorites.remove(label)
            console.print(f"[yellow]Removed from favorites.[/yellow]")
        else:
            favorites.append(label)
            console.print(f"[green]Added to favorites.[/green]")

    config["favorites"] = favorites
    save_config(config)


def main():
    os.system("clear" if os.name != "nt" else "cls")
    _auto_cleanup(console)
    show_dashboard(console)

    while True:
        menu_choices = _build_menu_choices()
        try:
            choice = inquirer.select(
                message="Select:",
                choices=menu_choices,
                pointer="❯",
            ).execute()
        except (KeyboardInterrupt, EOFError):
            break

        if choice == "Exit":
            console.print("[bold green]Goodbye![/bold green]")
            break
        elif choice == "Clear Screen":
            os.system("clear" if os.name != "nt" else "cls")
            show_dashboard(console)
            continue

        # Tool categories
        for cat in CATEGORIES:
            if choice.startswith(cat):
                _run_category(console, cat)
                break
        else:
            # Favorites (direct tool launch)
            if choice in HANDLERS:
                try:
                    HANDLERS[choice](console)
                except KeyboardInterrupt:
                    console.print("\n[yellow]Interrupted.[/yellow]")
                except FileNotFoundError as e:
                    tool_name = e.filename or "unknown"
                    console.print(f"\n[red]{tool_name} is not installed.[/red]")
                    console.print(f"[yellow]Install it with: brew install {tool_name}[/yellow]")
            elif choice == "Management":
                _management_submenu(console)
            elif choice == "Generate Report":
                generate_report(console)
            elif choice == "Cheat Sheets":
                cheatsheet_menu(console)
            elif choice == "Settings":
                config_menu(console)
            elif choice == "Manage Favorites":
                _manage_favorites(console)

        console.print()


if __name__ == "__main__":
    main()
