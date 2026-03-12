PLUGIN_NAME = "Directory Listing Checker"
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSION = "1.0"

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
    console.print(f"[dim]Checking {len(COMMON_DIRS)} common directories...[/dim]\n")

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

    console.print(f"\n[bold]{len(found)} directories with listing enabled[/bold]")
