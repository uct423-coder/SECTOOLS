import os
import urllib.request
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn
from InquirerPy import inquirer

from sectools.config import load_config, save_config

WORDLIST_DIR = Path.home() / "sectools-wordlists"
PROJECT_WORDLIST_DIR = Path(__file__).resolve().parent.parent.parent / "wordlists"

PRESET_WORDLISTS = {
    "rockyou.txt (passwords — 14M entries)": "https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt",
    "common.txt (dirb)": "https://raw.githubusercontent.com/v0re/dirb/master/wordlists/common.txt",
    "directory-list-2.3-small.txt": "https://raw.githubusercontent.com/daviddias/node-dirbuster/master/lists/directory-list-2.3-small.txt",
    "subdomains-top1million-5000.txt": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/DNS/subdomains-top1million-5000.txt",
    "top-usernames-shortlist.txt": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Usernames/top-usernames-shortlist.txt",
    "default-passwords.txt": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Default-Credentials/default-passwords.txt",
    "common-web-passwords.txt (10k)": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10k-most-common.txt",
    "Custom URL...": None,
}


def _get_all_wordlists() -> list[Path]:
    """Collect all .txt wordlists from both directories."""
    files = []
    for d in (WORDLIST_DIR, PROJECT_WORDLIST_DIR):
        if d.is_dir():
            files.extend(sorted(d.glob("*.txt")))
    return files


def _file_line_count(path: Path) -> int:
    count = 0
    with open(path, "r", errors="ignore") as f:
        for _ in f:
            count += 1
    return count


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _list_wordlists(console: Console):
    files = _get_all_wordlists()
    if not files:
        console.print("[yellow]No wordlists found.[/yellow]")
        return

    table = Table(title="Wordlists", border_style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Location")
    table.add_column("Lines", justify="right")
    table.add_column("Size", justify="right")

    for f in files:
        table.add_row(
            f.name,
            str(f.parent),
            str(_file_line_count(f)),
            _human_size(f.stat().st_size),
        )
    console.print(table)


def _download_wordlist(console: Console):
    choice = inquirer.select(
        message="Select wordlist to download:",
        choices=list(PRESET_WORDLISTS.keys()),
        pointer="❯",
    ).execute()

    if choice == "Custom URL...":
        url = inquirer.text(message="Enter URL:").execute()
        if not url:
            return
        filename = url.rsplit("/", 1)[-1] or "downloaded.txt"
    else:
        url = PRESET_WORDLISTS[choice]
        filename = url.rsplit("/", 1)[-1]

    WORDLIST_DIR.mkdir(parents=True, exist_ok=True)
    dest = WORDLIST_DIR / filename

    if dest.exists():
        overwrite = inquirer.confirm(
            message=f"{filename} already exists. Overwrite?", default=False
        ).execute()
        if not overwrite:
            return

    console.print(f"[cyan]Downloading:[/cyan] {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SecTools/1.0"})
        resp = urllib.request.urlopen(req)
        total = int(resp.headers.get("Content-Length", 0))

        with Progress(
            "[progress.description]{task.description}",
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Downloading", total=total or None)
            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    progress.advance(task, len(chunk))

        console.print(f"[green]Saved to {dest}[/green]")
    except Exception as e:
        console.print(f"[red]Download failed: {e}[/red]")


def _wordlist_stats(console: Console):
    files = _get_all_wordlists()
    if not files:
        console.print("[yellow]No wordlists found.[/yellow]")
        return

    choice = inquirer.select(
        message="Select wordlist:",
        choices=[f.name for f in files],
        pointer="❯",
    ).execute()

    path = next(f for f in files if f.name == choice)
    stat = path.stat()

    with open(path, "r", errors="ignore") as f:
        lines = f.readlines()

    total = len(lines)
    unique = len(set(line.strip() for line in lines))
    first_5 = [l.rstrip("\n") for l in lines[:5]]
    last_5 = [l.rstrip("\n") for l in lines[-5:]]

    table = Table(title=f"Stats: {path.name}", border_style="dim")
    table.add_column("Metric", style="bold")
    table.add_column("Value")
    table.add_row("Path", str(path))
    table.add_row("File size", _human_size(stat.st_size))
    table.add_row("Total lines", str(total))
    table.add_row("Unique entries", str(unique))
    table.add_row("First 5", "\n".join(first_5))
    table.add_row("Last 5", "\n".join(last_5))
    console.print(table)


def _set_default(console: Console):
    files = _get_all_wordlists()
    if not files:
        console.print("[yellow]No wordlists found.[/yellow]")
        return

    choice = inquirer.select(
        message="Select default wordlist:",
        choices=[f.name for f in files],
        pointer="❯",
    ).execute()

    path = next(f for f in files if f.name == choice)
    config = load_config()
    config["default_wordlist"] = str(path)
    save_config(config)
    console.print(f"[green]Default wordlist set to {path}[/green]")


def run(console: Console):
    """Wordlist manager entry point."""
    WORDLIST_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        action = inquirer.select(
            message="Wordlist Manager:",
            choices=[
                "List Wordlists",
                "Download Wordlist",
                "Wordlist Stats",
                "Set Default",
                "Back",
            ],
            pointer="❯",
        ).execute()

        if action == "List Wordlists":
            _list_wordlists(console)
        elif action == "Download Wordlist":
            _download_wordlist(console)
        elif action == "Wordlist Stats":
            _wordlist_stats(console)
        elif action == "Set Default":
            _set_default(console)
        else:
            return
