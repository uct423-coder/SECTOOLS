import subprocess
from InquirerPy import inquirer
from rich.console import Console
from sectools.utils import run_logged

PRESETS = {
    "Basic scan": [],
    "Enumerate databases (--dbs)": ["--dbs"],
    "Enumerate tables (-D <db> --tables)": "tables",
    "Dump table (-D <db> -T <table> --dump)": "dump",
    "Custom flags": None,
}


def run(console: Console):
    console.rule("[bold cyan]SQLMap[/bold cyan]")

    url = inquirer.text(message="Target URL (with parameter, e.g. http://target/page?id=1):").execute()
    if not url.strip():
        console.print("[red]No URL provided.[/red]")
        return

    if "?" not in url:
        console.print("[yellow]Warning: URL has no query parameters (e.g. ?id=1). SQLMap needs a parameter to test.[/yellow]")

    preset = inquirer.select(
        message="Scan type:",
        choices=list(PRESETS.keys()) + ["View cheat sheet"],
        pointer="❯",
    ).execute()

    if preset == "View cheat sheet":
        from sectools.cheatsheets import show_cheatsheet
        show_cheatsheet(console, "sqlmap")
        return

    flags = []
    val = PRESETS[preset]
    if val is None:
        flags_str = inquirer.text(message="Enter sqlmap flags:").execute()
        flags = flags_str.split()
    elif val == "tables":
        db = inquirer.text(message="Database name:").execute()
        flags = ["-D", db.strip(), "--tables"]
    elif val == "dump":
        db = inquirer.text(message="Database name:").execute()
        table = inquirer.text(message="Table name:").execute()
        flags = ["-D", db.strip(), "-T", table.strip(), "--dump"]
    else:
        flags = val

    cmd = ["sqlmap", "-u", url.strip(), "--batch"] + flags
    run_logged(cmd, console, "sqlmap")
