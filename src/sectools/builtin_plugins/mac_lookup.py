PLUGIN_NAME = "MAC Address Lookup"
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSION = "1.0"

import urllib.request
import json
from InquirerPy import inquirer


def run(console):
    console.rule("[bold cyan]MAC Address Lookup[/bold cyan]")
    mac = inquirer.text(message="MAC address (e.g. AA:BB:CC:DD:EE:FF):").execute().strip()
    if not mac:
        console.print("[red]No input.[/red]")
        return

    prefix = mac.replace(":", "").replace("-", "").replace(".", "")[:6].upper()
    console.print(f"[dim]Looking up OUI prefix {prefix}...[/dim]\n")

    try:
        url = f"https://api.maclookup.app/v2/macs/{prefix}"
        req = urllib.request.Request(url, headers={"User-Agent": "SecTools/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get("found"):
                console.print(f"  [bold]Vendor:[/bold]  {data.get('company', 'Unknown')}")
                console.print(f"  [bold]Country:[/bold] {data.get('country', 'Unknown')}")
            else:
                console.print("[yellow]MAC prefix not found in database.[/yellow]")
    except Exception as e:
        console.print(f"[red]Lookup failed: {e}[/red]")
