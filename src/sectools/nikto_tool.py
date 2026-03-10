import subprocess
from InquirerPy import inquirer
from rich.console import Console
from sectools.utils import extract_hostname, run_logged, ask_target

PRESETS = {
    "Standard scan": [],
    "Scan specific port": "port",
    "With SSL (-ssl)": ["-ssl"],
    "Custom flags": None,
}


def run(console: Console):
    console.print("\n[bold cyan]━━━ Nikto — Web Server Scanner ━━━[/bold cyan]\n")

    target = ask_target(console, "Target host (IP/hostname/URL):")
    if not target:
        return

    hostname, was_url = extract_hostname(target)
    if was_url:
        console.print(f"[yellow]Extracted hostname: {hostname}[/yellow]")

    preset = inquirer.select(
        message="Scan type:",
        choices=list(PRESETS.keys()) + ["View cheat sheet"],
        pointer="❯",
    ).execute()

    if preset == "View cheat sheet":
        from sectools.cheatsheets import show_cheatsheet
        show_cheatsheet(console, "nikto")
        return

    flags = []
    val = PRESETS[preset]
    if val is None:
        flags_str = inquirer.text(message="Enter nikto flags:").execute()
        flags = flags_str.split()
    elif val == "port":
        port = inquirer.text(message="Port number:").execute()
        flags = ["-p", port.strip()]
    else:
        flags = val

    cmd = ["nikto", "-h", hostname] + flags
    run_logged(cmd, console, "nikto")
