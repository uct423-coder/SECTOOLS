PLUGIN_NAME = "Ping Sweep"
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSION = "1.0"

import subprocess
import ipaddress
from InquirerPy import inquirer


def run(console):
    console.rule("[bold cyan]Ping Sweep[/bold cyan]")
    cidr = inquirer.text(message="Subnet (e.g. 192.168.1.0/24):").execute().strip()
    if not cidr:
        console.print("[red]No input.[/red]")
        return

    try:
        network = ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        console.print("[red]Invalid CIDR notation.[/red]")
        return

    hosts = list(network.hosts())
    if len(hosts) > 256:
        console.print(f"[yellow]Warning: {len(hosts)} hosts. This may take a while.[/yellow]")

    console.print(f"[dim]Sweeping {len(hosts)} hosts...[/dim]\n")
    alive = []
    for ip in hosts:
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "1", str(ip)],
                capture_output=True, timeout=3,
            )
            if result.returncode == 0:
                console.print(f"  [green][+][/green] {ip} is alive")
                alive.append(str(ip))
        except (subprocess.TimeoutExpired, Exception):
            pass

    console.print(f"\n[bold]{len(alive)}/{len(hosts)} hosts alive[/bold]")
