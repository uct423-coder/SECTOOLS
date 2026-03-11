import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.utils import run_logged

PRESETS = {
    "Quick scan (--aggression 1)": ["--aggression", "1"],
    "Standard scan (--aggression 3)": ["--aggression", "3"],
    "Aggressive scan (--aggression 4)": ["--aggression", "4"],
    "Verbose output (-v)": ["-v"],
    "Custom flags": None,
}


def run(console: Console):
    console.rule("[bold cyan]WhatWeb — Technology Identifier[/bold cyan]", style="cyan")
    console.print()

    target = inquirer.text(message="Target URL:").execute()
    if not target or not target.strip():
        console.print("[red]No target provided.[/red]")
        return
    target = target.strip()

    preset = inquirer.select(
        message="Scan type:",
        choices=list(PRESETS.keys()) + ["View cheat sheet"],
        pointer="❯",
    ).execute()

    if preset == "View cheat sheet":
        from sectools.cheatsheets import show_cheatsheet
        show_cheatsheet(console, "whatweb")
        return

    if PRESETS[preset] is None:
        flags_str = inquirer.text(message="Enter whatweb flags:").execute()
        flags = shlex.split(flags_str)
    else:
        flags = PRESETS[preset]

    cmd = ["whatweb"] + flags + [target]
    run_logged(cmd, console, "whatweb")
