PLUGIN_NAME = "DNS Resolver"
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSION = "1.0"

import subprocess
from InquirerPy import inquirer


RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "ANY"]


def run(console):
    console.rule("[bold cyan]DNS Resolver[/bold cyan]")
    domain = inquirer.text(message="Domain:").execute().strip()
    if not domain:
        console.print("[red]No domain.[/red]")
        return

    rtype = inquirer.select(
        message="Record type:",
        choices=RECORD_TYPES,
        pointer="\u276f",
    ).execute()

    console.print(f"\n[dim]Resolving {rtype} for {domain}...[/dim]\n")
    try:
        result = subprocess.run(
            ["dig", "+short", domain, rtype],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout.strip()
        if output:
            for line in output.splitlines():
                console.print(f"  [green]{line}[/green]")
        else:
            console.print("[yellow]No records found.[/yellow]")
    except FileNotFoundError:
        console.print("[red]dig not installed.[/red]")
