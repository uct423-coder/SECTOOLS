import shlex
from pathlib import Path
from InquirerPy import inquirer
from rich.console import Console
from sectools.utils import run_logged, pick_wordlist, WORDLISTS_DIR

PRESETS = {
    "Crack with default wordlist": [],
    "Crack with custom wordlist": "wordlist",
    "Show cracked passwords (--show)": ["--show"],
    "Incremental mode (brute force)": ["--incremental"],
    "Custom flags": None,
}


def run(console: Console):
    console.rule("[bold cyan]John the Ripper — Password Cracker[/bold cyan]", style="cyan")
    console.print()

    hashfile = inquirer.text(message="Hash file path:").execute().strip()
    if not hashfile:
        console.print("[red]No hash file provided.[/red]")
        return
    if not Path(hashfile).exists():
        console.print(f"[yellow]Warning: {hashfile} not found.[/yellow]")

    preset = inquirer.select(
        message="Mode:",
        choices=list(PRESETS.keys()) + ["View cheat sheet"],
        pointer="❯",
    ).execute()

    if preset == "View cheat sheet":
        from sectools.cheatsheets import show_cheatsheet
        show_cheatsheet(console, "john")
        return

    val = PRESETS[preset]
    if val is None:
        flags_str = inquirer.text(message="Enter john flags:").execute()
        flags = shlex.split(flags_str)
    elif val == "wordlist":
        wordlist = pick_wordlist("Wordlist:", str(WORDLISTS_DIR / "rockyou.txt"))
        flags = [f"--wordlist={wordlist}"]
    else:
        flags = val

    cmd = ["john"] + flags + [hashfile]
    run_logged(cmd, console, "john")
