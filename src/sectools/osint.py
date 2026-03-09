"""OSINT Module — subdomain enumeration, reverse IP, HTTP headers."""

import json
import urllib.request
import urllib.error
import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from InquirerPy import inquirer

from sectools.utils import LOGS_DIR

TIMEOUT = 10


def _subdomain_enum(console: Console):
    """Query crt.sh for subdomains via certificate transparency."""
    domain = inquirer.text(message="Domain:").execute().strip()
    if not domain:
        console.print("[red]No domain provided.[/red]")
        return

    console.print(f"[dim]Querying crt.sh for {domain}...[/dim]")
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SecTools/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    # Deduplicate
    subdomains = sorted({entry.get("name_value", "").strip() for entry in data} - {""})

    if not subdomains:
        console.print("[yellow]No subdomains found.[/yellow]")
        return

    table = Table(title=f"Subdomains for {domain}", border_style="dim")
    table.add_column("#", style="dim")
    table.add_column("Subdomain", style="cyan")
    for i, sub in enumerate(subdomains, 1):
        table.add_row(str(i), sub)
    console.print(table)
    console.print(f"[green]{len(subdomains)} unique subdomains found.[/green]")

    _offer_save(console, f"osint_subdomains_{domain}", "\n".join(subdomains))


def _reverse_ip(console: Console):
    """Query HackerTarget reverse IP lookup."""
    ip = inquirer.text(message="IP address:").execute().strip()
    if not ip:
        console.print("[red]No IP provided.[/red]")
        return

    console.print(f"[dim]Querying HackerTarget for {ip}...[/dim]")
    url = f"https://api.hackertarget.com/reverseiplookup/?q={ip}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SecTools/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            result = resp.read().decode().strip()
    except (urllib.error.URLError, TimeoutError) as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    if not result or "error" in result.lower():
        console.print(f"[yellow]{result or 'No results found.'}[/yellow]")
        return

    domains = result.splitlines()
    table = Table(title=f"Reverse IP: {ip}", border_style="dim")
    table.add_column("#", style="dim")
    table.add_column("Domain", style="cyan")
    for i, d in enumerate(domains, 1):
        table.add_row(str(i), d)
    console.print(table)

    _offer_save(console, f"osint_reverseip_{ip}", result)


def _http_headers(console: Console):
    """Fetch and display HTTP headers for a URL."""
    url = inquirer.text(message="URL:").execute().strip()
    if not url:
        console.print("[red]No URL provided.[/red]")
        return
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    console.print(f"[dim]Fetching headers for {url}...[/dim]")
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "SecTools/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            headers = resp.headers
    except (urllib.error.URLError, TimeoutError) as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    table = Table(title=f"HTTP Headers: {url}", border_style="dim")
    table.add_column("Header", style="cyan")
    table.add_column("Value", style="white")
    header_text = []
    for key, value in headers.items():
        table.add_row(key, value)
        header_text.append(f"{key}: {value}")
    console.print(table)

    _offer_save(console, "osint_headers", "\n".join(header_text))


def _offer_save(console: Console, prefix: str, content: str):
    """Optionally save results to a log file."""
    save = inquirer.confirm(message="Save results to log?", default=False).execute()
    if save:
        LOGS_DIR.mkdir(exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = LOGS_DIR / f"{prefix}_{ts}.log"
        path.write_text(content)
        console.print(f"[green]Saved to {path}[/green]")


def run(console: Console):
    """OSINT sub-menu."""
    while True:
        action = inquirer.select(
            message="OSINT:",
            choices=[
                "Subdomain Enumeration (crt.sh)",
                "Reverse IP Lookup (HackerTarget)",
                "HTTP Headers",
                "Back",
            ],
            pointer="❯",
        ).execute()

        if action.startswith("Subdomain"):
            _subdomain_enum(console)
        elif action.startswith("Reverse"):
            _reverse_ip(console)
        elif action.startswith("HTTP"):
            _http_headers(console)
        else:
            break
