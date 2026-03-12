PLUGIN_NAME = "JWT Decoder"
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSION = "1.0"

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

        console.print("\n[bold cyan]Header:[/bold cyan]")
        console.print_json(json.dumps(header, indent=2))

        console.print("\n[bold cyan]Payload:[/bold cyan]")
        console.print_json(json.dumps(payload, indent=2))

        console.print(f"\n[bold cyan]Signature:[/bold cyan] [dim]{parts[2][:40]}...[/dim]")

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
