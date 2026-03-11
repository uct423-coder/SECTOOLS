import shlex
from InquirerPy import inquirer
from rich.console import Console
from sectools.utils import run_logged, ask_target

PRESETS = {
    "Standard scan": [],
    "Show certificate": ["--show-certificate"],
    "No color (--no-colour)": ["--no-colour"],
    "Check specific protocol (--tls10/--tls11/--tls12/--tls13)": None,
    "Custom flags": None,
}

PROTOCOL_CHOICES = [
    "--tls10",
    "--tls11",
    "--tls12",
    "--tls13",
]


def run(console: Console):
    console.rule("[bold cyan]SSLScan — TLS/SSL Analyzer[/bold cyan]", style="cyan")
    console.print()

    target = ask_target(console, "Host:port (e.g. example.com:443):")
    if not target:
        return

    preset = inquirer.select(
        message="Scan type:",
        choices=list(PRESETS.keys()),
        pointer="❯",
    ).execute()

    if preset == "Check specific protocol (--tls10/--tls11/--tls12/--tls13)":
        protocol = inquirer.select(
            message="Select protocol:",
            choices=PROTOCOL_CHOICES,
            pointer="❯",
        ).execute()
        flags = [protocol]
    elif preset == "Custom flags":
        flags_str = inquirer.text(message="Enter sslscan flags:").execute()
        flags = shlex.split(flags_str)
    else:
        flags = PRESETS[preset]

    cmd = ["sslscan"] + flags + [target]
    run_logged(cmd, console, "sslscan")
