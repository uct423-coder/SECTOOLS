import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.utils import run_logged, ask_target

PRESETS = {
    "Default templates": [],
    "Critical & High severity (-s critical,high)": ["-s", "critical,high"],
    "CVE templates (-t cves/)": ["-t", "cves/"],
    "Exposed panels (-t exposed-panels/)": ["-t", "exposed-panels/"],
    "Misconfigurations (-t misconfiguration/)": ["-t", "misconfiguration/"],
    "Technologies (-t technologies/)": ["-t", "technologies/"],
    "Full scan (all templates)": ["-as"],
    "Custom flags": None,
}

SEVERITIES = ["(skip)", "info", "low", "medium", "high", "critical"]


def run(console: Console):
    console.rule("[bold cyan]Nuclei — Vulnerability Scanner[/bold cyan]", style="cyan")
    console.print()

    target = ask_target(console, "Target URL/host:")
    if not target:
        return

    preset = inquirer.select(
        message="Scan preset:",
        choices=list(PRESETS.keys()) + ["View cheat sheet"],
        pointer="❯",
    ).execute()

    if preset == "View cheat sheet":
        from sectools.cheatsheets import show_cheatsheet
        show_cheatsheet(console, "nuclei")
        return

    if PRESETS[preset] is None:
        flags_str = inquirer.text(message="Enter nuclei flags:").execute()
        flags = shlex.split(flags_str)
    else:
        flags = list(PRESETS[preset])

    severity = inquirer.select(
        message="Severity filter:",
        choices=SEVERITIES,
        pointer="❯",
    ).execute()

    if severity != "(skip)":
        flags += ["-s", severity]

    cmd = ["nuclei", "-u", target] + flags
    run_logged(cmd, console, "nuclei")
