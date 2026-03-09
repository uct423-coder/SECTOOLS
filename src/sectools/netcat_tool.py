import subprocess
from InquirerPy import inquirer
from rich.console import Console

MODES = {
    "Listen for connections": "listen",
    "Connect to host": "connect",
    "Port scan": "scan",
}


def run(console: Console):
    console.rule("[bold cyan]Netcat — Network Swiss Army Knife[/bold cyan]")

    mode = inquirer.select(
        message="Mode:",
        choices=list(MODES.keys()),
        pointer="❯",
    ).execute()
    action = MODES[mode]

    if action == "listen":
        port = inquirer.text(message="Port to listen on:").execute().strip()
        if not port:
            console.print("[red]No port provided.[/red]")
            return
        cmd = ["nc", "-lvnp", port]
    elif action == "connect":
        host = inquirer.text(message="Target host:").execute().strip()
        port = inquirer.text(message="Target port:").execute().strip()
        if not host or not port:
            console.print("[red]Host and port required.[/red]")
            return
        cmd = ["nc", "-v", host, port]
    else:
        host = inquirer.text(message="Target host:").execute().strip()
        port_range = inquirer.text(message="Port range (e.g. 1-1000):").execute().strip()
        if not host or not port_range:
            console.print("[red]Host and port range required.[/red]")
            return
        cmd = ["nc", "-zv", host, port_range]

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]\n")
    subprocess.run(cmd)
