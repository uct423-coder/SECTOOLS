import importlib.util
import urllib.request
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from InquirerPy import inquirer

PLUGINS_DIR = Path.home() / ".sectools-plugins"

# Built-in plugin store — plugins users can install with one click
PLUGIN_STORE = {
    "Whois Lookup": {
        "description": "Look up domain registration info (whois)",
        "filename": "whois_lookup.py",
        "code": '''\
PLUGIN_NAME = "Whois Lookup"

import subprocess
from InquirerPy import inquirer


def run(console):
    console.rule("[bold cyan]Whois Lookup[/bold cyan]")
    domain = inquirer.text(message="Domain or IP:").execute().strip()
    if not domain:
        console.print("[red]No input.[/red]")
        return
    console.print(f"[dim]Looking up {domain}...[/dim]\\n")
    try:
        result = subprocess.run(["whois", domain], capture_output=True, text=True, timeout=15)
        console.print(result.stdout or result.stderr or "[yellow]No results.[/yellow]")
    except FileNotFoundError:
        console.print("[red]whois not installed. Install with: brew install whois[/red]")
    except subprocess.TimeoutExpired:
        console.print("[red]Lookup timed out.[/red]")
''',
    },
    "DNS Resolver": {
        "description": "Resolve DNS records (A, AAAA, MX, NS, TXT, CNAME)",
        "filename": "dns_resolver.py",
        "code": '''\
PLUGIN_NAME = "DNS Resolver"

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
        pointer="\\u276f",
    ).execute()

    console.print(f"\\n[dim]Resolving {rtype} for {domain}...[/dim]\\n")
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
''',
    },
    "Ping Sweep": {
        "description": "Ping a range of IPs to find live hosts",
        "filename": "ping_sweep.py",
        "code": '''\
PLUGIN_NAME = "Ping Sweep"

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

    console.print(f"[dim]Sweeping {len(hosts)} hosts...[/dim]\\n")
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

    console.print(f"\\n[bold]{len(alive)}/{len(hosts)} hosts alive[/bold]")
''',
    },
    "MAC Address Lookup": {
        "description": "Identify device vendor from a MAC address",
        "filename": "mac_lookup.py",
        "code": '''\
PLUGIN_NAME = "MAC Address Lookup"

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
    console.print(f"[dim]Looking up OUI prefix {prefix}...[/dim]\\n")

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
''',
    },
    "JWT Decoder": {
        "description": "Decode and inspect JSON Web Tokens",
        "filename": "jwt_decoder.py",
        "code": '''\
PLUGIN_NAME = "JWT Decoder"

import base64
import json
from InquirerPy import inquirer


def _b64decode(s):
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s).decode("utf-8")


def run(console):
    console.rule("[bold cyan]JWT Decoder[/bold cyan]")
    token = inquirer.text(message="Paste JWT token:").execute().strip()
    if not token:
        console.print("[red]No input.[/red]")
        return

    parts = token.split(".")
    if len(parts) != 3:
        console.print("[red]Invalid JWT — expected 3 dot-separated parts.[/red]")
        return

    try:
        header = json.loads(_b64decode(parts[0]))
        payload = json.loads(_b64decode(parts[1]))

        console.print("\\n[bold cyan]Header:[/bold cyan]")
        console.print_json(json.dumps(header, indent=2))

        console.print("\\n[bold cyan]Payload:[/bold cyan]")
        console.print_json(json.dumps(payload, indent=2))

        console.print(f"\\n[bold cyan]Signature:[/bold cyan] [dim]{parts[2][:40]}...[/dim]")

        if "exp" in payload:
            import datetime
            exp = datetime.datetime.fromtimestamp(payload["exp"])
            now = datetime.datetime.now()
            if exp < now:
                console.print(f"[red]Token EXPIRED on {exp}[/red]")
            else:
                console.print(f"[green]Token valid until {exp}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to decode: {e}[/red]")
''',
    },
    "SSL Certificate Checker": {
        "description": "Check SSL/TLS certificate details for a domain",
        "filename": "ssl_checker.py",
        "code": '''\
PLUGIN_NAME = "SSL Certificate Checker"

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

    console.print(f"[dim]Checking SSL cert for {domain}...[/dim]\\n")
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
            console.print(f"\\n  [bold red]EXPIRED {abs(days_left)} days ago![/bold red]")
        elif days_left < 30:
            console.print(f"\\n  [bold yellow]Expires in {days_left} days![/bold yellow]")
        else:
            console.print(f"\\n  [bold green]{days_left} days until expiry[/bold green]")

    except Exception as e:
        console.print(f"[red]Failed: {e}[/red]")
''',
    },
    "Directory Listing Checker": {
        "description": "Check if a web server has directory listing enabled",
        "filename": "dirlist_checker.py",
        "code": '''\
PLUGIN_NAME = "Directory Listing Checker"

import urllib.request
from InquirerPy import inquirer


COMMON_DIRS = [
    "/", "/images/", "/uploads/", "/css/", "/js/", "/assets/",
    "/backup/", "/admin/", "/tmp/", "/data/", "/files/",
    "/docs/", "/media/", "/static/", "/public/", "/private/",
]


def run(console):
    console.rule("[bold cyan]Directory Listing Checker[/bold cyan]")
    url = inquirer.text(message="Base URL (e.g. https://target.com):").execute().strip()
    if not url:
        console.print("[red]No URL.[/red]")
        return

    url = url.rstrip("/")
    console.print(f"[dim]Checking {len(COMMON_DIRS)} common directories...[/dim]\\n")

    found = []
    for d in COMMON_DIRS:
        target = f"{url}{d}"
        try:
            req = urllib.request.Request(target, headers={"User-Agent": "SecTools/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read(4096).decode("utf-8", errors="ignore").lower()
                if "index of" in body or "directory listing" in body or "<pre>" in body:
                    console.print(f"  [red][OPEN][/red]   {target}")
                    found.append(target)
                else:
                    console.print(f"  [green][OK][/green]     {target}")
        except Exception:
            console.print(f"  [dim][SKIP][/dim]   {target}")

    console.print(f"\\n[bold]{len(found)} directories with listing enabled[/bold]")
''',
    },
    "Tech Stack Detector": {
        "description": "Detect web technologies from HTTP headers and HTML",
        "filename": "tech_detect.py",
        "code": '''\
PLUGIN_NAME = "Tech Stack Detector"

import urllib.request
import re
from InquirerPy import inquirer


HEADER_SIGS = {
    "x-powered-by": "Powered By",
    "server": "Server",
    "x-aspnet-version": "ASP.NET",
    "x-drupal-cache": "Drupal",
    "x-generator": "Generator",
    "x-shopify-stage": "Shopify",
}

BODY_SIGS = [
    (r"wp-content|wp-includes|wordpress", "WordPress"),
    (r"Joomla", "Joomla"),
    (r"Drupal\\.settings", "Drupal"),
    (r"shopify\\.com", "Shopify"),
    (r"react", "React"),
    (r"vue\\.js|vuejs", "Vue.js"),
    (r"angular", "Angular"),
    (r"jquery", "jQuery"),
    (r"bootstrap", "Bootstrap"),
    (r"tailwindcss|tailwind", "Tailwind CSS"),
    (r"next\\.js|nextjs|_next/", "Next.js"),
    (r"nuxt", "Nuxt.js"),
    (r"laravel", "Laravel"),
    (r"django", "Django"),
    (r"flask", "Flask"),
    (r"express", "Express.js"),
    (r"cloudflare", "Cloudflare"),
    (r"google-analytics|gtag", "Google Analytics"),
    (r"recaptcha", "reCAPTCHA"),
]


def run(console):
    console.rule("[bold cyan]Tech Stack Detector[/bold cyan]")
    url = inquirer.text(message="URL:").execute().strip()
    if not url:
        console.print("[red]No URL.[/red]")
        return
    if not url.startswith("http"):
        url = f"https://{url}"

    console.print(f"[dim]Scanning {url}...[/dim]\\n")
    detected = []

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            headers = dict(resp.headers)
            body = resp.read(50000).decode("utf-8", errors="ignore")

            # Check headers
            for hdr, label in HEADER_SIGS.items():
                val = headers.get(hdr) or headers.get(hdr.title())
                if val:
                    detected.append((label, val))

            # Check body
            for pattern, name in BODY_SIGS:
                if re.search(pattern, body, re.IGNORECASE):
                    detected.append((name, "Detected in HTML"))

    except Exception as e:
        console.print(f"[red]Failed: {e}[/red]")
        return

    if detected:
        seen = set()
        for tech, detail in detected:
            if tech not in seen:
                console.print(f"  [green][+][/green] [bold]{tech}[/bold] — {detail}")
                seen.add(tech)
        console.print(f"\\n[bold]{len(seen)} technologies detected[/bold]")
    else:
        console.print("[yellow]No technologies detected.[/yellow]")
''',
    },
}


def discover_plugins() -> list[dict]:
    """Find valid plugins in the plugins directory."""
    if not PLUGINS_DIR.exists():
        return []

    plugins = []
    for f in sorted(PLUGINS_DIR.glob("*.py")):
        try:
            spec = importlib.util.spec_from_file_location(f.stem, f)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "PLUGIN_NAME") and hasattr(mod, "run"):
                plugins.append({"name": mod.PLUGIN_NAME, "run": mod.run, "path": f})
        except Exception:
            continue
    return plugins


def _install_plugin(console: Console, name: str, info: dict):
    """Install a plugin from the store."""
    PLUGINS_DIR.mkdir(exist_ok=True)
    dest = PLUGINS_DIR / info["filename"]
    if dest.exists():
        console.print(f"[yellow]{name} is already installed.[/yellow]")
        return
    dest.write_text(info["code"])
    console.print(f"[green]Installed {name} to {dest}[/green]")


def _uninstall_plugin(console: Console):
    """Uninstall an installed plugin."""
    plugins = discover_plugins()
    if not plugins:
        console.print("[yellow]No plugins installed.[/yellow]")
        return
    choices = [p["name"] for p in plugins] + ["Back"]
    choice = inquirer.select(message="Uninstall which plugin?", choices=choices, pointer="❯").execute()
    if choice == "Back":
        return
    plugin = next(p for p in plugins if p["name"] == choice)
    plugin["path"].unlink()
    console.print(f"[green]Uninstalled {choice}.[/green]")


def plugins_menu(console: Console):
    """Plugin hub — run, install, or uninstall plugins."""
    PLUGINS_DIR.mkdir(exist_ok=True)

    while True:
        choice = inquirer.select(
            message="Plugins:",
            choices=[
                "Run a Plugin",
                "Install from Store",
                "Uninstall a Plugin",
                "Back",
            ],
            pointer="❯",
        ).execute()

        if choice == "Back":
            return

        elif choice == "Run a Plugin":
            plugins = discover_plugins()
            if not plugins:
                console.print("[yellow]No plugins installed. Install some from the store![/yellow]")
                continue
            names = [p["name"] for p in plugins] + ["Back"]
            pick = inquirer.select(message="Select plugin:", choices=names, pointer="❯").execute()
            if pick == "Back":
                continue
            plugin = next(p for p in plugins if p["name"] == pick)
            try:
                plugin["run"](console)
            except Exception as e:
                console.print(f"[red]Plugin error: {e}[/red]")

        elif choice == "Install from Store":
            installed_names = {p["name"] for p in discover_plugins()}
            table = Table(title="Plugin Store", border_style="cyan")
            table.add_column("#", style="cyan", width=3)
            table.add_column("Plugin", style="bold")
            table.add_column("Description")
            table.add_column("Status")

            store_items = list(PLUGIN_STORE.items())
            for i, (name, info) in enumerate(store_items, 1):
                status = "[green]Installed[/green]" if name in installed_names else "[dim]Not installed[/dim]"
                table.add_row(str(i), name, info["description"], status)
            console.print(table)

            available = [n for n in PLUGIN_STORE if n not in installed_names]
            if not available:
                console.print("[green]All plugins installed![/green]")
                continue

            picks = available + ["Install All", "Back"]
            pick = inquirer.select(message="Install:", choices=picks, pointer="❯").execute()
            if pick == "Back":
                continue
            elif pick == "Install All":
                for name in available:
                    _install_plugin(console, name, PLUGIN_STORE[name])
                console.print(f"[bold green]Installed {len(available)} plugins.[/bold green]")
            else:
                _install_plugin(console, pick, PLUGIN_STORE[pick])

        elif choice == "Uninstall a Plugin":
            _uninstall_plugin(console)

        console.print()


def get_plugin_menu_items() -> list[str]:
    """Return menu item strings for discovered plugins."""
    plugins = discover_plugins()
    return [f"Plugin: {p['name']}" for p in plugins]
