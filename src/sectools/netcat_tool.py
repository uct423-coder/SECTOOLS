import os
import shutil
import subprocess
from InquirerPy import inquirer
from rich.console import Console


def _valid_port(port: str) -> bool:
    return port.isdigit() and 1 <= int(port) <= 65535

MODES = {
    "Listen for connections": "listen",
    "Connect to host": "connect",
    "Port scan": "scan",
}


def run(console: Console):
    console.rule("[bold cyan]Netcat — Network Swiss Army Knife[/bold cyan]", style="cyan")
    console.print()

    mode = inquirer.select(
        message="Mode:",
        choices=list(MODES.keys()) + ["View cheat sheet"],
        pointer="❯",
    ).execute()

    if mode == "View cheat sheet":
        from sectools.cheatsheets import show_cheatsheet
        show_cheatsheet(console, "netcat")
        return

    action = MODES[mode]

    # Use ncat on Windows, nc on macOS/Linux
    nc = "ncat" if (os.name == "nt" or (shutil.which("ncat") and not shutil.which("nc"))) else "nc"

    if action == "listen":
        port = inquirer.text(message="Port to listen on:").execute().strip()
        if not port or not _valid_port(port):
            console.print("[red]Invalid port. Must be 1-65535.[/red]")
            return
        cmd = [nc, "-lvnp", port]
    elif action == "connect":
        host = inquirer.text(message="Target host:").execute().strip()
        port = inquirer.text(message="Target port:").execute().strip()
        if not host or not port or not _valid_port(port):
            console.print("[red]Host and valid port (1-65535) required.[/red]")
            return
        cmd = [nc, "-v", host, port]
    else:
        host = inquirer.text(message="Target host:").execute().strip()
        port_range = inquirer.text(message="Port range (e.g. 1-1000):").execute().strip()
        if not host or not port_range:
            console.print("[red]Host and port range required.[/red]")
            return
        cmd = [nc, "-zv", host, port_range]

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]\n")
    subprocess.run(cmd)
