import subprocess
from InquirerPy import inquirer
from rich.console import Console
from sectools.utils import run_logged

MODES = {
    "Directory brute-force (dir)": "dir",
    "DNS subdomain brute-force (dns)": "dns",
    "Virtual host brute-force (vhost)": "vhost",
}

from pathlib import Path

def _find_wordlist() -> str:
    """Find common.txt wordlist, checking several likely locations."""
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "wordlists" / "common.txt",
        Path.home() / "wordlists" / "common.txt",
        Path("/usr/share/wordlists/dirb/common.txt"),
        Path("/usr/share/seclists/Discovery/Web-Content/common.txt"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return str(candidates[0])  # fallback to repo-relative

DEFAULT_WORDLIST = _find_wordlist()


def run(console: Console):
    console.rule("[bold cyan]Gobuster — Directory & DNS Brute Force[/bold cyan]")

    mode = inquirer.select(
        message="Mode:",
        choices=list(MODES.keys()) + ["View cheat sheet"],
        pointer="❯",
    ).execute()

    if mode == "View cheat sheet":
        from sectools.cheatsheets import show_cheatsheet
        show_cheatsheet(console, "gobuster")
        return

    mode_flag = MODES[mode]

    if mode_flag == "dir":
        url = inquirer.text(message="Target URL (e.g. https://target.com):").execute().strip()
        if not url:
            console.print("[red]No URL provided.[/red]")
            return
        wordlist = inquirer.text(
            message="Wordlist path:",
            default=DEFAULT_WORDLIST,
        ).execute().strip()
        extensions = inquirer.text(message="File extensions (e.g. php,html,txt) or leave empty:").execute().strip()
        cmd = ["gobuster", "dir", "-u", url, "-w", wordlist]
        if extensions:
            cmd += ["-x", extensions]
    elif mode_flag == "dns":
        domain = inquirer.text(message="Target domain (e.g. target.com):").execute().strip()
        if not domain:
            console.print("[red]No domain provided.[/red]")
            return
        wordlist = inquirer.text(
            message="Wordlist path:",
            default=DEFAULT_WORDLIST,
        ).execute().strip()
        cmd = ["gobuster", "dns", "-d", domain, "-w", wordlist]
    else:
        url = inquirer.text(message="Target URL:").execute().strip()
        if not url:
            console.print("[red]No URL provided.[/red]")
            return
        wordlist = inquirer.text(
            message="Wordlist path:",
            default=DEFAULT_WORDLIST,
        ).execute().strip()
        cmd = ["gobuster", "vhost", "-u", url, "-w", wordlist]

    threads = inquirer.text(message="Threads (default 10):", default="10").execute().strip()
    cmd += ["-t", threads]

    run_logged(cmd, console, "gobuster")
