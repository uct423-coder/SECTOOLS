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
    wpscan_tool, ffuf_tool, nuclei_tool, enum4linux_tool, whatweb_tool,
    dns_tool, whois_tool, sslscan_tool, masscan_tool, subfinder_tool,
    wafw00f_tool, dirb_tool,
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
from sectools import osint, screenshot, cred_manager, scope, sessions, assessment
from sectools import workflows
from sectools.proxy import proxy_menu
from sectools.onboarding import needs_onboarding, run_onboarding
from sectools.theme import bold, rule_style, primary

console = Console()

# ── Category sub-menus ──────────────────────────────────────────────

CATEGORIES = {
    "Recon & OSINT": [
        ("Recon Autopilot", recon_tool.run),
        ("Nmap — Network Scanner", nmap_tool.run),
        ("Nikto — Web Server Scanner", nikto_tool.run),
        ("OSINT — Subdomain & Recon", osint.run),
        ("Subfinder — Subdomain Discovery", subfinder_tool.run),
        ("WhatWeb — Technology ID", whatweb_tool.run),
        ("Whois — Domain Lookup", whois_tool.run),
        ("DNS Toolkit", dns_tool.run),
        ("Security Assessment Wizard", assessment.run),
    ],
    "Exploitation": [
        ("Metasploit — Framework", msf_tool.run),
        ("SQLMap — SQL Injection", sqlmap_tool.run),
        ("Hydra — Brute Force", hydra_tool.run),
        ("WPScan — WordPress Scanner", wpscan_tool.run),
        ("Nuclei — Vulnerability Scanner", nuclei_tool.run),
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
        ("Masscan — Fast Port Scanner", masscan_tool.run),
        ("SSLScan — TLS Analyzer", sslscan_tool.run),
        ("Wafw00f — WAF Detector", wafw00f_tool.run),
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
        ("Enum4Linux — SMB Enumeration", enum4linux_tool.run),
    ],
    "Fuzzing & Brute Force": [
        ("Ffuf — Web Fuzzer", ffuf_tool.run),
        ("Dirb — URL Brute Forcer", dirb_tool.run),
        ("Gobuster — Dir & DNS Brute Force", gobuster_tool.run),
    ],
}

# Flat lookup for favorites
ALL_TOOL_ITEMS = []
HANDLERS = {}
for _cat, _tools in CATEGORIES.items():
    for _label, _handler in _tools:
        ALL_TOOL_ITEMS.append((_cat, _label, _handler))
        HANDLERS[_label] = _handler


SHORTCUTS = {
    "n": "Nmap — Network Scanner",
    "k": "Nikto — Web Server Scanner",
    "g": "Gobuster — Dir & DNS Brute Force",
    "r": "Recon Autopilot",
    "o": "OSINT — Subdomain & Recon",
    "m": "Metasploit — Framework",
    "s": "SQLMap — SQL Injection",
    "h": "Hydra — Brute Force",
    "j": "John the Ripper",
    "c": "Hashcat — GPU Cracker",
    "t": "Netcat — Network Swiss Army Knife",
    "p": "HTTP Probe — Quick URL Scanner",
    "x": "Screenshot — Capture Web Pages",
    "a": "Security Assessment Wizard",
    "w": "WPScan — WordPress Scanner",
    "f": "Ffuf — Web Fuzzer",
    "u": "Nuclei — Vulnerability Scanner",
    "d": "DNS Toolkit",
    "e": "Enum4Linux — SMB Enumeration",
    "i": "Masscan — Fast Port Scanner",
}


def _quick_launch(console: Console):
    """Quick launch a tool via keyboard shortcut."""
    from rich.table import Table
    from sectools.theme import border_style as th_border
    table = Table(title="Quick Launch Shortcuts", border_style=th_border(), padding=(0, 2))
    table.add_column("Key", style="bold cyan", justify="center")
    table.add_column("Tool")
    for key, tool in SHORTCUTS.items():
        table.add_row(key, tool)
    table.add_row("q", "[dim]Cancel[/dim]")
    console.print(table)

    key = inquirer.text(message="Press key:").execute().strip().lower()
    if key == "q" or not key:
        return

    tool_name = SHORTCUTS.get(key)
    if tool_name and tool_name in HANDLERS:
        try:
            HANDLERS[tool_name](console)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/yellow]")
        except FileNotFoundError as e:
            name = e.filename or "unknown"
            console.print(f"\n[red]{name} is not installed.[/red]")
    else:
        console.print(f"[yellow]Unknown shortcut: {key}[/yellow]")


def _run_category(console: Console, category: str):
    """Show a sub-menu for a tool category."""
    tools = CATEGORIES[category]
    choices = [t[0] for t in tools] + ["Back"]
    cat_icons = {
        "Recon & OSINT": "🔍", "Exploitation": "💥", "Password Cracking": "🔑",
        "Networking & Web": "🌐", "Generators": "⚙️ ", "Analysis": "📊",
    }
    icon = cat_icons.get(category, "")
    console.rule(bold(f"{icon} {category}"), style=rule_style())

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
        choices.append(Separator("╭─── ★ Favorites ───╮"))
        for fav in favorites:
            choices.append(fav)
        choices.append(Separator("╰───────────────────╯"))

    # Tool categories with emoji indicators
    choices.append(Separator("┌─── Tools ─────────────────────┐"))
    cat_icons = {
        "Recon & OSINT": "🔍",
        "Exploitation": "💥",
        "Password Cracking": "🔑",
        "Networking & Web": "🌐",
        "Generators": "⚙️ ",
        "Analysis": "📊",
        "Fuzzing & Brute Force": "🔨",
    }
    for cat in CATEGORIES:
        icon = cat_icons.get(cat, "")
        count = len(CATEGORIES[cat])
        choices.append(f"{icon} {cat}  ({count})")
    choices.append(Separator("└───────────────────────────────┘"))

    # Other
    choices.append(Separator("┌─── Actions ───────────────────┐"))
    choices.extend([
        "🔗 Workflows",
        "🗂️  Management",
        "📝 Generate Report",
        "📖 Cheat Sheets",
        "⚙️  Settings",
        "🌐 Proxy Settings",
        "⚡ Quick Launch",
        "★  Manage Favorites",
        "Clear Screen",
        "Exit",
    ])
    choices.append(Separator("└───────────────────────────────┘"))

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
                "🎯 Targets & Groups",
                "📋 Scans & Profiles",
                "🔒 Security",
                "🖥️  System",
                "Back",
            ],
            pointer="❯",
        ).execute()

        if choice == "Back":
            return
        elif "Targets" in choice:
            _targets_submenu(console)
        elif "Scans" in choice:
            _scans_submenu(console)
        elif "Security" in choice:
            _security_submenu(console)
        elif "System" in choice:
            _system_submenu(console)
        console.print()


def _targets_submenu(console: Console):
    config = load_config()
    theme = config.get("theme_color", "cyan")
    while True:
        choice = inquirer.select(
            message="Targets & Groups:",
            choices=["View Saved Targets", "Edit Target Notes", "Target Groups", "Back"],
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
        console.print()


def _scans_submenu(console: Console):
    while True:
        choice = inquirer.select(
            message="Scans & Profiles:",
            choices=["Scan Profiles", "Wordlist Manager", "Schedule a Scan", "View Scheduled Scans", "Back"],
            pointer="❯",
        ).execute()
        if choice == "Back":
            return
        elif choice == "Scan Profiles":
            scan_profiles.run(console)
        elif choice == "Wordlist Manager":
            wordlist_mgr.run(console)
        elif choice == "Schedule a Scan":
            schedule_scan(console)
        elif choice == "View Scheduled Scans":
            view_scheduled(console)
        console.print()


def _security_submenu(console: Console):
    while True:
        choice = inquirer.select(
            message="Security:",
            choices=["Scope Manager", "Credential Manager", "Sessions", "Back"],
            pointer="❯",
        ).execute()
        if choice == "Back":
            return
        elif choice == "Scope Manager":
            scope.run(console)
        elif choice == "Credential Manager":
            cred_manager.run(console)
        elif choice == "Sessions":
            sessions.run(console)
        console.print()


def _system_submenu(console: Console):
    while True:
        choice = inquirer.select(
            message="System:",
            choices=["Tool Status", "Install Missing Tools", "Plugins", "Back"],
            pointer="❯",
        ).execute()
        if choice == "Back":
            return
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
    console.clear()
    if needs_onboarding():
        run_onboarding(console)
    _auto_cleanup(console)
    show_dashboard(console)

    while True:
        menu_choices = _build_menu_choices()
        console.print("[dim]SecTools v2.1.0 │ Ctrl+C to interrupt │ ↑↓ to navigate[/dim]")
        try:
            choice = inquirer.select(
                message="Select:",
                choices=menu_choices,
                pointer="❯",
            ).execute()
        except (KeyboardInterrupt, EOFError):
            break

        if choice == "Exit":
            console.print("\n  [bold green]✔[/bold green] [dim]Goodbye![/dim]\n")
            break
        elif choice == "Clear Screen":
            console.clear()
            show_dashboard(console)
            continue

        # Tool categories — match by category name in the choice string
        matched = False
        for cat in CATEGORIES:
            if cat in choice:
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
            elif "Workflows" in choice:
                workflows.run(console)
            elif "Proxy" in choice:
                proxy_menu(console)
            elif "Management" in choice:
                _management_submenu(console)
            elif "Report" in choice:
                generate_report(console)
            elif "Cheat" in choice:
                cheatsheet_menu(console)
            elif "Settings" in choice:
                config_menu(console)
            elif "Quick Launch" in choice:
                _quick_launch(console)
            elif "Favorites" in choice:
                _manage_favorites(console)

        console.print()


if __name__ == "__main__":
    main()
