import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.utils import run_logged, ask_target

PRESETS = {
    "Full enumeration (-a)": ["-a"],
    "User enumeration (-U)": ["-U"],
    "Share enumeration (-S)": ["-S"],
    "Password policy (-P)": ["-P"],
    "Group enumeration (-G)": ["-G"],
    "OS info (-o)": ["-o"],
    "Custom flags": None,
}


def run(console: Console):
    console.rule("[bold cyan]Enum4Linux — SMB Enumeration[/bold cyan]", style="cyan")
    console.print()

    target = ask_target(console, "Target IP:")
    if not target:
        return

    preset = inquirer.select(
        message="Enumeration type:",
        choices=list(PRESETS.keys()) + ["View cheat sheet"],
        pointer="❯",
    ).execute()

    if preset == "View cheat sheet":
        from sectools.cheatsheets import show_cheatsheet
        show_cheatsheet(console, "enum4linux")
        return

    if PRESETS[preset] is None:
        flags_str = inquirer.text(message="Enter enum4linux flags:").execute()
        flags = shlex.split(flags_str)
    else:
        flags = PRESETS[preset]

    cmd = ["enum4linux"] + flags + [target]
    run_logged(cmd, console, "enum4linux")
