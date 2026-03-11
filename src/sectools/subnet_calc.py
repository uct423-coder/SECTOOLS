"""IP/Subnet Calculator — parse CIDR and display network details."""

import ipaddress

from InquirerPy import inquirer
from rich.console import Console
from rich.table import Table


def _ip_class(network: ipaddress.IPv4Network) -> str:
    first_octet = int(network.network_address.packed[0])
    if first_octet < 128:
        return "A"
    if first_octet < 192:
        return "B"
    if first_octet < 224:
        return "C"
    if first_octet < 240:
        return "D (Multicast)"
    return "E (Reserved)"


def run(console: Console) -> None:
    """Calculate subnet details from CIDR notation."""
    console.rule("[bold cyan]IP / Subnet Calculator[/bold cyan]", style="cyan")
    console.print()

    cidr = inquirer.text(message="Enter CIDR (e.g. 192.168.1.0/24):").execute()
    if not cidr:
        console.print("[red]No input provided.[/red]")
        return

    try:
        net = ipaddress.ip_network(cidr.strip(), strict=False)
    except ValueError as exc:
        console.print(f"[red]Invalid CIDR: {exc}[/red]")
        return

    if isinstance(net, ipaddress.IPv6Network):
        total = net.num_addresses
        usable = max(total - 2, 0) if net.prefixlen < 127 else total
        if total > 2**20:
            # Avoid enumerating huge networks; calculate first/last directly
            first_usable = str(net.network_address + 1)
            last_usable = str(net.broadcast_address - 1) if net.prefixlen < 127 else str(net.broadcast_address)
        else:
            hosts = list(net.hosts())
            first_usable = str(hosts[0]) if hosts else "N/A"
            last_usable = str(hosts[-1]) if hosts else "N/A"
        ip_cls = "IPv6"
        wildcard = "N/A"
    else:
        total = net.num_addresses
        usable = max(total - 2, 0)
        if net.prefixlen < 31:
            first_usable = str(net.network_address + 1)
            last_usable = str(net.broadcast_address - 1)
        else:
            hosts = list(net)
            first_usable = str(hosts[0]) if hosts else "N/A"
            last_usable = str(hosts[-1]) if hosts else "N/A"
        wildcard = str(ipaddress.IPv4Address(int(net.hostmask)))
        ip_cls = _ip_class(net)

    table = Table(title=f"Subnet Details — {net}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Network Address", str(net.network_address))
    table.add_row("Broadcast Address", str(net.broadcast_address))
    table.add_row("Subnet Mask", str(net.netmask))
    table.add_row("Wildcard Mask", wildcard)
    table.add_row("Prefix Length", f"/{net.prefixlen}")
    table.add_row("Total Hosts", f"{total:,}")
    table.add_row("Usable Hosts", f"{usable:,}")
    table.add_row("First Usable Host", first_usable)
    table.add_row("Last Usable Host", last_usable)
    table.add_row("IP Class", ip_cls)

    console.print(table)
