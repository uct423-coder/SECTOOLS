PLUGIN_NAME = "Whois Lookup"
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSION = "1.0"

import subprocess
from InquirerPy import inquirer


def run(console):
    console.rule("[bold cyan]Whois Lookup[/bold cyan]")
    domain = inquirer.text(message="Domain or IP:").execute().strip()
    if not domain:
        console.print("[red]No input.[/red]")
        return
    console.print(f"[dim]Looking up {domain}...[/dim]\n")
    try:
        result = subprocess.run(["whois", domain], capture_output=True, text=True, timeout=15)
        console.print(result.stdout or result.stderr or "[yellow]No results.[/yellow]")
    except FileNotFoundError:
        console.print("[red]whois not installed. Install with: brew install whois[/red]")
    except subprocess.TimeoutExpired:
        console.print("[red]Lookup timed out.[/red]")
