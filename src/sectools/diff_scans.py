import difflib
from pathlib import Path
from rich.console import Console
from rich.text import Text
from InquirerPy import inquirer
from sectools.utils import LOGS_DIR


def diff_scans(console: Console):
    """Pick two log files and show a colored unified diff."""
    if not LOGS_DIR.exists():
        console.print("[red]No logs found.[/red]")
        return

    logs = sorted(LOGS_DIR.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
    if len(logs) < 2:
        console.print("[red]Need at least 2 scan logs to diff.[/red]")
        return

    names = [f.name for f in logs]

    first = inquirer.select(message="First scan:", choices=names, pointer="❯").execute()
    second = inquirer.select(message="Second scan:", choices=names, pointer="❯").execute()

    if first == second:
        console.print("[yellow]Same file selected twice.[/yellow]")
        return

    a_lines = (LOGS_DIR / first).read_text().splitlines(keepends=True)
    b_lines = (LOGS_DIR / second).read_text().splitlines(keepends=True)

    diff = list(difflib.unified_diff(a_lines, b_lines, fromfile=first, tofile=second))

    if not diff:
        console.print("[green]No differences found.[/green]")
        return

    console.rule("[bold cyan]Diff[/bold cyan]")
    for line in diff:
        line = line.rstrip("\n")
        if line.startswith("+++") or line.startswith("---"):
            console.print(f"[bold]{line}[/bold]")
        elif line.startswith("+"):
            console.print(f"[green]{line}[/green]")
        elif line.startswith("-"):
            console.print(f"[red]{line}[/red]")
        elif line.startswith("@@"):
            console.print(f"[cyan]{line}[/cyan]")
        else:
            console.print(line)
