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
from sectools.utils import show_tool_status, generate_report, load_targets, TARGETS_FILE

console = Console()

BANNER = r"""
   _____ ______  ______ ______  ____   ____  __   _____
  / ___// ____/ / ____//_  __/ / __ \ / __ \/ /  / ___/
  \__ \/ __/   / /      / /   / / / // / / // /   \__ \
 ___/ / /___  / /___   / /   / /_/ // /_/ // /______/ /
/____/_____/  \____/  /_/    \____/ \____//_____/____/
"""

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
    Separator("── Utilities ──"),
    "Netcat — Network Swiss Army Knife",
    Separator("── Other ──"),
    "Tool Status — Check installed tools",
    "View Saved Targets",
    "Generate Report",
    "Clear Screen",
    "Exit",
]

HANDLERS = {
    "Recon Autopilot — Auto-scan a target": recon_tool.run,
    "Nmap — Network Scanner": nmap_tool.run,
    "Nikto — Web Server Scanner": nikto_tool.run,
    "Gobuster — Directory & DNS Brute Force": gobuster_tool.run,
    "Metasploit — Exploitation Framework": msf_tool.run,
    "SQLMap — SQL Injection Tester": sqlmap_tool.run,
    "Hydra — Brute Force": hydra_tool.run,
    "John the Ripper — Password Cracker": john_tool.run,
    "Hashcat — GPU Password Cracker": hashcat_tool.run,
    "Netcat — Network Swiss Army Knife": netcat_tool.run,
}


def view_targets(console: Console):
    targets = load_targets()
    if not targets:
        console.print("[yellow]No saved targets yet.[/yellow]")
        return
    console.rule("[bold cyan]Saved Targets[/bold cyan]")
    for i, t in enumerate(targets, 1):
        console.print(f"  [cyan]{i}.[/cyan] {t}")
    console.print(f"\n[dim]Stored in {TARGETS_FILE}[/dim]")


def main():
    os.system("clear" if os.name != "nt" else "cls")
    console.print(Panel(Text(BANNER, style="bold cyan"), title="Security Toolkit", border_style="bright_blue"))
    console.print("[dim]Educational security testing toolkit. Use responsibly.[/dim]\n")

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
        elif choice == "Generate Report":
            generate_report(console)
        elif choice == "Clear Screen":
            os.system("clear" if os.name != "nt" else "cls")
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
