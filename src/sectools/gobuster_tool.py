from InquirerPy import inquirer
from rich.console import Console
from sectools.utils import run_logged, pick_wordlist, WORDLISTS_DIR

MODES = {
    "Directory brute-force (dir)": "dir",
    "DNS subdomain brute-force (dns)": "dns",
    "Virtual host brute-force (vhost)": "vhost",
}

from sectools.config import load_config


def run(console: Console):
    console.print("\n[bold cyan]━━━ Gobuster — Dir & DNS Brute Force ━━━[/bold cyan]\n")

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
        wordlist = pick_wordlist("Wordlist:", load_config().get("default_dirwordlist", str(WORDLISTS_DIR / "common.txt")))
        extensions = inquirer.text(message="File extensions (e.g. php,html,txt) or leave empty:").execute().strip()
        cmd = ["gobuster", "dir", "-u", url, "-w", wordlist]
        if extensions:
            cmd += ["-x", extensions]
    elif mode_flag == "dns":
        domain = inquirer.text(message="Target domain (e.g. target.com):").execute().strip()
        if not domain:
            console.print("[red]No domain provided.[/red]")
            return
        wordlist = pick_wordlist("Wordlist:", load_config().get("default_dirwordlist", str(WORDLISTS_DIR / "common.txt")))
        cmd = ["gobuster", "dns", "-d", domain, "-w", wordlist]
    else:
        url = inquirer.text(message="Target URL:").execute().strip()
        if not url:
            console.print("[red]No URL provided.[/red]")
            return
        wordlist = pick_wordlist("Wordlist:", load_config().get("default_dirwordlist", str(WORDLISTS_DIR / "common.txt")))
        cmd = ["gobuster", "vhost", "-u", url, "-w", wordlist]

    threads = inquirer.text(message="Threads (default 10):", default="10").execute().strip()
    cmd += ["-t", threads]

    run_logged(cmd, console, "gobuster")
