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

# ── ANSI color helpers ──────────────────────────────────────────────

_CYAN = "\033[36m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_MAGENTA = "\033[35m"
_BLUE = "\033[34m"
_WHITE = "\033[97m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

# ── Category sub-menus ──────────────────────────────────────────────

CATEGORIES = {
    "Recon & OSINT": [
        (f"{_CYAN}Recon Autopilot{_RESET}", recon_tool.run),
        (f"{_CYAN}Nmap{_RESET} — Network Scanner", nmap_tool.run),
        (f"{_CYAN}Nikto{_RESET} — Web Server Scanner", nikto_tool.run),
        (f"{_CYAN}Gobuster{_RESET} — Dir & DNS Brute Force", gobuster_tool.run),
        (f"{_CYAN}OSINT{_RESET} — Subdomain & Recon", osint.run),
    ],
    "Exploitation": [
        (f"{_RED}Metasploit{_RESET} — Framework", msf_tool.run),
        (f"{_RED}SQLMap{_RESET} — SQL Injection", sqlmap_tool.run),
        (f"{_RED}Hydra{_RESET} — Brute Force", hydra_tool.run),
    ],
    "Password Cracking": [
        (f"{_YELLOW}John the Ripper{_RESET}", john_tool.run),
        (f"{_YELLOW}Hashcat{_RESET} — GPU Cracker", hashcat_tool.run),
    ],
    "Networking & Web": [
        (f"{_GREEN}Netcat{_RESET} — Network Swiss Army Knife", netcat_tool.run),
        (f"{_GREEN}HTTP Probe{_RESET} — Quick URL Scanner", http_probe.run),
        (f"{_GREEN}Screenshot{_RESET} — Capture Web Pages", screenshot.run),
        (f"{_GREEN}Port Reference{_RESET}", port_ref.run),
        (f"{_GREEN}Subnet Calculator{_RESET}", subnet_calc.run),
    ],
    "Generators": [
        (f"{_MAGENTA}Reverse Shell Generator{_RESET}", revshell.run),
        (f"{_MAGENTA}Password Generator{_RESET}", passgen.run),
        (f"{_MAGENTA}Encoding / Decoding{_RESET}", encoding.run),
    ],
    "Analysis": [
        (f"{_BLUE}Hash Identifier{_RESET}", hash_id.run),
        (f"{_BLUE}Scan History Browser{_RESET}", scan_history.run),
        (f"{_BLUE}Diff Scans{_RESET}", lambda c: diff_scans(c)),
    ],
}

# Color mapping for category labels in main menu
_CAT_COLORS = {
    "Recon & OSINT": _CYAN,
    "Exploitation": _RED,
    "Password Cracking": _YELLOW,
    "Networking & Web": _GREEN,
    "Generators": _MAGENTA,
    "Analysis": _BLUE,
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
    choices = [t[0] for t in tools] + [f"{_DIM}Back{_RESET}"]

    while True:
        choice = inquirer.select(
            message=f"{category}:",
            choices=choices,
            pointer="❯",
        ).execute()

        if _strip_ansi(choice) == "Back":
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
        color = _CAT_COLORS.get(cat, "")
        count = len(CATEGORIES[cat])
        choices.append(f"{color}{cat}{_RESET}  {_DIM}({count}){_RESET}")

    # Other
    choices.append(Separator("──────────"))
    choices.extend([
        f"{_WHITE}Management{_RESET}",
        f"{_GREEN}Generate Report{_RESET}",
        f"{_CYAN}Cheat Sheets{_RESET}",
        f"{_YELLOW}Settings{_RESET}",
        f"{_MAGENTA}Manage Favorites{_RESET}",
        f"{_DIM}Clear Screen{_RESET}",
        f"{_RED}Exit{_RESET}",
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
    """Management sub-menu — compact categories."""
    while True:
        choice = inquirer.select(
            message="Management:",
            choices=[
                f"{_CYAN}Targets & Groups{_RESET}",
                f"{_BLUE}Scans & Profiles{_RESET}",
                f"{_RED}Security{_RESET}",
                f"{_YELLOW}System{_RESET}",
                f"{_DIM}Back{_RESET}",
            ],
            pointer="❯",
        ).execute()

        clean = _strip_ansi(choice)
        if clean == "Back":
            return
        elif clean == "Targets & Groups":
            _targets_submenu(console)
        elif clean == "Scans & Profiles":
            _scans_submenu(console)
        elif clean == "Security":
            _security_submenu(console)
        elif clean == "System":
            _system_submenu(console)
        console.print()


def _targets_submenu(console: Console):
    config = load_config()
    theme = config.get("theme_color", "cyan")
    while True:
        choice = inquirer.select(
            message="Targets & Groups:",
            choices=[
                f"{_CYAN}View Saved Targets{_RESET}",
                f"{_CYAN}Edit Target Notes{_RESET}",
                f"{_CYAN}Target Groups{_RESET}",
                f"{_DIM}Back{_RESET}",
            ],
            pointer="❯",
        ).execute()
        clean = _strip_ansi(choice)
        if clean == "Back":
            return
        elif clean == "View Saved Targets":
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
        elif clean == "Edit Target Notes":
            edit_target_notes(console)
        elif clean == "Target Groups":
            target_groups.run(console)
        console.print()


def _scans_submenu(console: Console):
    while True:
        choice = inquirer.select(
            message="Scans & Profiles:",
            choices=[
                f"{_BLUE}Scan Profiles{_RESET}",
                f"{_BLUE}Wordlist Manager{_RESET}",
                f"{_BLUE}Schedule a Scan{_RESET}",
                f"{_BLUE}View Scheduled Scans{_RESET}",
                f"{_DIM}Back{_RESET}",
            ],
            pointer="❯",
        ).execute()
        clean = _strip_ansi(choice)
        if clean == "Back":
            return
        elif clean == "Scan Profiles":
            scan_profiles.run(console)
        elif clean == "Wordlist Manager":
            wordlist_mgr.run(console)
        elif clean == "Schedule a Scan":
            schedule_scan(console)
        elif clean == "View Scheduled Scans":
            view_scheduled(console)
        console.print()


def _security_submenu(console: Console):
    while True:
        choice = inquirer.select(
            message="Security:",
            choices=[
                f"{_RED}Scope Manager{_RESET}",
                f"{_RED}Credential Manager{_RESET}",
                f"{_RED}Sessions{_RESET}",
                f"{_DIM}Back{_RESET}",
            ],
            pointer="❯",
        ).execute()
        clean = _strip_ansi(choice)
        if clean == "Back":
            return
        elif clean == "Scope Manager":
            scope.run(console)
        elif clean == "Credential Manager":
            cred_manager.run(console)
        elif clean == "Sessions":
            sessions.run(console)
        console.print()


def _system_submenu(console: Console):
    while True:
        choice = inquirer.select(
            message="System:",
            choices=[
                f"{_YELLOW}Tool Status{_RESET}",
                f"{_YELLOW}Install Missing Tools{_RESET}",
                f"{_YELLOW}Plugins{_RESET}",
                f"{_DIM}Back{_RESET}",
            ],
            pointer="❯",
        ).execute()
        clean = _strip_ansi(choice)
        if clean == "Back":
            return
        elif clean == "Tool Status":
            show_tool_status(console)
        elif clean == "Install Missing Tools":
            auto_installer.run(console)
        elif clean == "Plugins":
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


def _strip_ansi(s: str) -> str:
    """Remove ANSI escape codes from a string."""
    import re
    return re.sub(r'\033\[[0-9;]*m', '', s)


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

        clean = _strip_ansi(choice)

        if clean.startswith("Exit"):
            console.print("[bold green]Goodbye![/bold green]")
            break
        elif clean.startswith("Clear Screen"):
            os.system("clear" if os.name != "nt" else "cls")
            show_dashboard(console)
            continue

        # Tool categories
        matched = False
        for cat in CATEGORIES:
            if clean.startswith(cat):
                _run_category(console, cat)
                matched = True
                break

        if not matched:
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
            elif clean.startswith("Management"):
                _management_submenu(console)
            elif clean.startswith("Generate Report"):
                generate_report(console)
            elif clean.startswith("Cheat Sheets"):
                cheatsheet_menu(console)
            elif clean.startswith("Settings"):
                config_menu(console)
            elif clean.startswith("Manage Favorites"):
                _manage_favorites(console)

        console.print()


if __name__ == "__main__":
    main()
