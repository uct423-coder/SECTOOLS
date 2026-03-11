import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.utils import run_logged, ask_target

PRESETS = {
    "Enumerate plugins (--enumerate p)": ["--enumerate", "p"],
    "Enumerate users (--enumerate u)": ["--enumerate", "u"],
    "Enumerate themes (--enumerate t)": ["--enumerate", "t"],
    "Full enumeration (--enumerate ap,at,u)": ["--enumerate", "ap,at,u"],
    "Aggressive plugin detection (--enumerate p --plugins-detection aggressive)": [
        "--enumerate", "p", "--plugins-detection", "aggressive",
    ],
    "Custom flags": None,
}


def run(console: Console):
    console.rule("[bold cyan]WPScan — WordPress Scanner[/bold cyan]", style="cyan")
    console.print()

    target = ask_target(console, "Target URL:")
    if not target:
        return

    preset = inquirer.select(
        message="Scan type:",
        choices=list(PRESETS.keys()) + ["View cheat sheet"],
        pointer="❯",
    ).execute()

    if preset == "View cheat sheet":
        from sectools.cheatsheets import show_cheatsheet
        show_cheatsheet(console, "wpscan")
        return

    if PRESETS[preset] is None:
        flags_str = inquirer.text(message="Enter wpscan flags:").execute()
        flags = shlex.split(flags_str)
    else:
        flags = PRESETS[preset]

    cmd = ["wpscan", "--url", target] + flags
    run_logged(cmd, console, "wpscan")
