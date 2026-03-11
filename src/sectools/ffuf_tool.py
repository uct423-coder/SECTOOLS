from InquirerPy import inquirer
from rich.console import Console
from sectools.utils import run_logged, pick_wordlist, WORDLISTS_DIR

MODES = {
    "Directory fuzzing": "dir",
    "Subdomain fuzzing (vhost)": "vhost",
    "Parameter fuzzing (GET)": "get",
    "Parameter fuzzing (POST)": "post",
    "Custom": "custom",
}

from sectools.config import load_config


def run(console: Console):
    console.rule("[bold cyan]Ffuf — Web Fuzzer[/bold cyan]", style="cyan")
    console.print()

    mode = inquirer.select(
        message="Mode:",
        choices=list(MODES.keys()) + ["View cheat sheet"],
        pointer="❯",
    ).execute()

    if mode == "View cheat sheet":
        from sectools.cheatsheets import show_cheatsheet
        show_cheatsheet(console, "ffuf")
        return

    mode_flag = MODES[mode]
    default_wordlist = load_config().get("default_dirwordlist", str(WORDLISTS_DIR / "common.txt"))

    if mode_flag == "dir":
        url = inquirer.text(message="Target URL with FUZZ keyword (e.g. https://target.com/FUZZ):").execute().strip()
        if not url:
            console.print("[red]No URL provided.[/red]")
            return
        wordlist = pick_wordlist("Wordlist:", default_wordlist)
        extensions = inquirer.text(message="File extensions (e.g. php,html,txt) or leave empty:").execute().strip()
        threads = inquirer.text(message="Threads (default 40):", default="40").execute().strip()
        cmd = ["ffuf", "-u", url, "-w", wordlist]
        if extensions:
            cmd += ["-e", extensions]
        cmd += ["-t", threads]

    elif mode_flag == "vhost":
        domain = inquirer.text(message="Target domain (e.g. https://target.com):").execute().strip()
        if not domain:
            console.print("[red]No domain provided.[/red]")
            return
        wordlist = pick_wordlist("Wordlist:", default_wordlist)
        threads = inquirer.text(message="Threads (default 40):", default="40").execute().strip()
        cmd = ["ffuf", "-u", domain, "-w", wordlist, "-H", "Host: FUZZ.target.com"]
        cmd += ["-t", threads]

    elif mode_flag == "get":
        url = inquirer.text(message="Target URL with FUZZ param (e.g. https://target.com/page?id=FUZZ):").execute().strip()
        if not url:
            console.print("[red]No URL provided.[/red]")
            return
        wordlist = pick_wordlist("Wordlist:", default_wordlist)
        threads = inquirer.text(message="Threads (default 40):", default="40").execute().strip()
        cmd = ["ffuf", "-u", url, "-w", wordlist]
        cmd += ["-t", threads]

    elif mode_flag == "post":
        url = inquirer.text(message="Target URL (e.g. https://target.com/login):").execute().strip()
        if not url:
            console.print("[red]No URL provided.[/red]")
            return
        wordlist = pick_wordlist("Wordlist:", default_wordlist)
        data = inquirer.text(message="POST data with FUZZ keyword (e.g. user=admin&pass=FUZZ):").execute().strip()
        if not data:
            console.print("[red]No POST data provided.[/red]")
            return
        threads = inquirer.text(message="Threads (default 40):", default="40").execute().strip()
        cmd = ["ffuf", "-u", url, "-w", wordlist, "-X", "POST", "-d", data]
        cmd += ["-t", threads]

    else:  # custom
        url = inquirer.text(message="Full ffuf command (without 'ffuf' prefix):").execute().strip()
        if not url:
            console.print("[red]No command provided.[/red]")
            return
        cmd = ["ffuf"] + url.split()

    run_logged(cmd, console, "ffuf")
