import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.utils import run_logged, ask_target

PRESETS = {
    "Detect WAF": [],
    "List all WAFs (wafw00f -l)": ["-l"],
    "Verbose (-v)": ["-v"],
    "Test all WAFs (-a)": ["-a"],
    "Custom flags": None,
}


def run(console: Console):
    console.rule("[bold cyan]Wafw00f — WAF Detector[/bold cyan]", style="cyan")
    console.print()

    target = ask_target(console, "Target URL:")
    if not target:
        return

    preset = inquirer.select(
        message="Scan type:",
        choices=list(PRESETS.keys()),
        pointer="❯",
    ).execute()

    if PRESETS[preset] is None:
        flags_str = inquirer.text(message="Enter wafw00f flags:").execute()
        flags = shlex.split(flags_str)
    else:
        flags = PRESETS[preset]

    if preset == "List all WAFs (wafw00f -l)":
        cmd = ["wafw00f"] + flags
    else:
        cmd = ["wafw00f"] + flags + [target]

    run_logged(cmd, console, "wafw00f")
