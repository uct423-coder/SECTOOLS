import subprocess
from pathlib import Path
from InquirerPy import inquirer
from rich.console import Console
from sectools.utils import extract_hostname, run_logged, ask_target

SERVICES = ["ssh", "ftp", "http-post-form", "smtp", "mysql", "rdp", "vnc", "telnet"]

WORDLISTS_DIR = Path.home() / ".sectools-wordlists"

# Default wordlist paths (downloaded by install.sh)
DEFAULT_PASSWORDS = str(WORDLISTS_DIR / "rockyou.txt")
DEFAULT_USERNAMES = str(WORDLISTS_DIR / "top-usernames-shortlist.txt")


def _pick_wordlist(message: str, default: str) -> str:
    """Let user pick a wordlist from downloaded ones or enter a custom path."""
    available = sorted(WORDLISTS_DIR.glob("*.txt")) if WORDLISTS_DIR.exists() else []

    if available:
        choices = [f.name for f in available] + ["Custom path..."]
        choice = inquirer.select(
            message=message,
            choices=choices,
            default=Path(default).name if Path(default).name in [f.name for f in available] else None,
            pointer="❯",
        ).execute()

        if choice == "Custom path...":
            return inquirer.text(message="Path:", default=default).execute().strip()
        return str(WORDLISTS_DIR / choice)

    return inquirer.text(message=message, default=default).execute().strip()


def run(console: Console):
    console.rule("[bold cyan]Hydra — Brute Force[/bold cyan]")

    target = ask_target(console, "Target (IP/hostname):")
    if not target:
        return

    hostname, was_url = extract_hostname(target)
    if was_url:
        console.print(f"[yellow]Extracted hostname: {hostname}[/yellow]")

    service = inquirer.select(
        message="Service to attack:",
        choices=SERVICES + ["View cheat sheet"],
        pointer="❯",
    ).execute()

    if service == "View cheat sheet":
        from sectools.cheatsheets import show_cheatsheet
        show_cheatsheet(console, "hydra")
        return

    mode = inquirer.select(
        message="Attack mode:",
        choices=["Username + password list", "Single user + password list", "Custom flags"],
        pointer="❯",
    ).execute()

    if mode == "Custom flags":
        flags_str = inquirer.text(message="Enter hydra flags:").execute()
        cmd = ["hydra"] + flags_str.split() + [hostname, service]
    elif mode == "Single user + password list":
        user = inquirer.text(message="Username:").execute().strip()
        wordlist = _pick_wordlist("Password wordlist:", DEFAULT_PASSWORDS)
        cmd = ["hydra", "-l", user, "-P", wordlist, hostname, service]
    else:
        userlist = _pick_wordlist("Username list:", DEFAULT_USERNAMES)
        wordlist = _pick_wordlist("Password wordlist:", DEFAULT_PASSWORDS)
        cmd = ["hydra", "-L", userlist, "-P", wordlist, hostname, service]

    run_logged(cmd, console, "hydra")
