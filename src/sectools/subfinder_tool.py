import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.utils import run_logged

PRESETS = {
    "Basic enumeration": [],
    "Silent mode (-silent)": ["-silent"],
    "Recursive (-recursive)": ["-recursive"],
    "All sources (-all)": ["-all"],
    "Custom flags": None,
}


def run(console: Console):
    console.rule("[bold cyan]Subfinder — Subdomain Discovery[/bold cyan]", style="cyan")
    console.print()

    domain = inquirer.text(message="Domain:").execute()
    if not domain:
        console.print("[red]No domain provided.[/red]")
        return

    preset = inquirer.select(
        message="Scan type:",
        choices=list(PRESETS.keys()),
        pointer="❯",
    ).execute()

    if PRESETS[preset] is None:
        flags_str = inquirer.text(message="Enter subfinder flags:").execute()
        flags = shlex.split(flags_str)
    else:
        flags = PRESETS[preset]

    threads = inquirer.text(
        message="Threads (default: 10):",
        default="10",
    ).execute()

    cmd = ["subfinder", "-d", domain] + flags + ["-t", threads]
    run_logged(cmd, console, "subfinder")
