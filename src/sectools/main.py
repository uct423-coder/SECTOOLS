import os
import sys

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
    edit_target_notes, TARGETS_FILE,
)
from sectools.cheatsheets import cheatsheet_menu
from sectools.diff_scans import diff_scans
from sectools.scheduler import schedule_scan, view_scheduled
from sectools.plugins import plugins_menu
from sectools.dashboard import show_dashboard
from sectools.config import config_menu
from sectools import (
    hash_id, revshell, encoding, port_ref,
    subnet_calc, passgen, http_probe,
    scan_history, wordlist_mgr, target_groups,
    scan_profiles, auto_installer,
)

console = Console()

MENU_CHOICES = [
    Separator("── Recon ──"),
    "Recon Autopilot — Auto-scan a target",
    "Nmap — Network Scanner",
    "Nikto — Web Server Scanner",
    "Gobuster — Directory & DNS Brute Force",
    Separator("── Exploitation ──"),
    "Metasploit — Exploitation Framework",
    "SQLMap — SQL Injection Tester",
    "Hydra — Brute Force",
    Separator("── Password Cracking ──"),
    "John the Ripper — Password Cracker",
    "Hashcat — GPU Password Cracker",
    Separator("── Networking ──"),
    "Netcat — Network Swiss Army Knife",
    "HTTP Probe — Quick URL Scanner",
    "Port Reference — Common Ports Lookup",
    "Subnet Calculator — IP/CIDR Math",
    Separator("── Generators ──"),
    "Reverse Shell Generator",
    "Password Generator",
    "Encoding / Decoding",
    Separator("── Analysis ──"),
    "Hash Identifier",
    "Scan History Browser",
    "Diff Scans",
    Separator("── Management ──"),
    "View Saved Targets",
    "Edit Target Notes",
    "Target Groups",
    "Scan Profiles",
    "Wordlist Manager",
    "Schedule a Scan",
    "View Scheduled Scans",
    Separator("── Other ──"),
    "Tool Status — Check installed tools",
    "Install Missing Tools",
    "Generate Report",
    "Cheat Sheets",
    "Settings",
    "Plugins",
    "Clear Screen",
    "Exit",
]

HANDLERS = {
    # Recon
    "Recon Autopilot — Auto-scan a target": recon_tool.run,
    "Nmap — Network Scanner": nmap_tool.run,
    "Nikto — Web Server Scanner": nikto_tool.run,
    "Gobuster — Directory & DNS Brute Force": gobuster_tool.run,
    # Exploitation
    "Metasploit — Exploitation Framework": msf_tool.run,
    "SQLMap — SQL Injection Tester": sqlmap_tool.run,
    "Hydra — Brute Force": hydra_tool.run,
    # Password Cracking
    "John the Ripper — Password Cracker": john_tool.run,
    "Hashcat — GPU Password Cracker": hashcat_tool.run,
    # Networking
    "Netcat — Network Swiss Army Knife": netcat_tool.run,
    "HTTP Probe — Quick URL Scanner": http_probe.run,
    "Port Reference — Common Ports Lookup": port_ref.run,
    "Subnet Calculator — IP/CIDR Math": subnet_calc.run,
    # Generators
    "Reverse Shell Generator": revshell.run,
    "Password Generator": passgen.run,
    "Encoding / Decoding": encoding.run,
    # Analysis
    "Hash Identifier": hash_id.run,
    "Scan History Browser": scan_history.run,
    "Diff Scans": lambda c: diff_scans(c),
    # Management
    "Target Groups": target_groups.run,
    "Scan Profiles": scan_profiles.run,
    "Wordlist Manager": wordlist_mgr.run,
    "Schedule a Scan": lambda c: schedule_scan(c),
    "View Scheduled Scans": lambda c: view_scheduled(c),
    # Other
    "Install Missing Tools": auto_installer.run,
    "Cheat Sheets": lambda c: cheatsheet_menu(c),
    "Settings": lambda c: config_menu(c),
    "Plugins": lambda c: plugins_menu(c),
}


def view_targets(console: Console):
    entries = load_targets_with_notes()
    if not entries:
        console.print("[yellow]No saved targets yet.[/yellow]")
        return
    console.rule("[bold cyan]Saved Targets[/bold cyan]")
    for i, e in enumerate(entries, 1):
        note = f" [dim]— {e['notes']}[/dim]" if e.get("notes") else ""
        group = f" [magenta][{e.get('group', '')}][/magenta]" if e.get("group") else ""
        console.print(f"  [cyan]{i}.[/cyan] {e['target']}{group}{note}")
    console.print(f"\n[dim]Stored in {TARGETS_FILE}[/dim]")


def main():
    os.system("clear" if os.name != "nt" else "cls")
    show_dashboard(console)

    while True:
        try:
            choice = inquirer.select(
                message="Select a tool:",
                choices=MENU_CHOICES,
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
