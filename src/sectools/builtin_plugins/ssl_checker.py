PLUGIN_NAME = "SSL Certificate Checker"
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSION = "1.0"

import ssl
import socket
import datetime
from InquirerPy import inquirer


def run(console):
    console.rule("[bold cyan]SSL Certificate Checker[/bold cyan]")
    domain = inquirer.text(message="Domain:").execute().strip()
    if not domain:
        console.print("[red]No input.[/red]")
        return

    console.print(f"[dim]Checking SSL cert for {domain}...[/dim]\n")
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(10)
            s.connect((domain, 443))
            cert = s.getpeercert()

        subject = dict(x[0] for x in cert.get("subject", []))
        issuer = dict(x[0] for x in cert.get("issuer", []))
        not_before = cert.get("notBefore", "")
        not_after = cert.get("notAfter", "")

        console.print(f"  [bold]Common Name:[/bold]  {subject.get('commonName', 'N/A')}")
        console.print(f"  [bold]Organization:[/bold] {subject.get('organizationName', 'N/A')}")
        console.print(f"  [bold]Issuer:[/bold]       {issuer.get('organizationName', 'N/A')}")
        console.print(f"  [bold]Valid From:[/bold]    {not_before}")
        console.print(f"  [bold]Valid Until:[/bold]   {not_after}")
        console.print(f"  [bold]Serial:[/bold]        {cert.get('serialNumber', 'N/A')}")

        # SANs
        sans = [v for t, v in cert.get("subjectAltName", []) if t == "DNS"]
        if sans:
            console.print(f"  [bold]SANs:[/bold]          {', '.join(sans[:5])}")
            if len(sans) > 5:
                console.print(f"                 [dim]... and {len(sans) - 5} more[/dim]")

        # Expiry check
        exp = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
        days_left = (exp - datetime.datetime.utcnow()).days
        if days_left < 0:
            console.print(f"\n  [bold red]EXPIRED {abs(days_left)} days ago![/bold red]")
        elif days_left < 30:
            console.print(f"\n  [bold yellow]Expires in {days_left} days![/bold yellow]")
        else:
            console.print(f"\n  [bold green]{days_left} days until expiry[/bold green]")

    except Exception as e:
        console.print(f"[red]Failed: {e}[/red]")
