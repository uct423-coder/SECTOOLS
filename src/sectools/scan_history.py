import os
import re
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from InquirerPy import inquirer

from sectools.utils import LOGS_DIR


def _get_logs() -> list[Path]:
    """Return all .log files in LOGS_DIR sorted newest first."""
    if not LOGS_DIR.exists():
        return []
    return sorted(LOGS_DIR.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True)


def _extract_tool_name(filename: str) -> str:
    """Extract the tool name from a log filename like 'nmap_target_20250101_120000.log'."""
    parts = filename.removesuffix(".log").split("_")
    # Tool name is everything before the first date-like segment (8 consecutive digits)
    tool_parts: list[str] = []
    for part in parts:
        if re.fullmatch(r"\d{8}", part):
            break
        tool_parts.append(part)
    return "_".join(tool_parts) if tool_parts else filename


def _format_date(path: Path) -> str:
    mtime = path.stat().st_mtime
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")


def _format_size(path: Path) -> str:
    size = path.stat().st_size
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"


def _show_table(console: Console, logs: list[Path]):
    """Display a Rich table of all scan logs."""
    table = Table(title="📋 Scan History", show_lines=False, border_style="dim")
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Filename", style="cyan")
    table.add_column("Tool", style="bold")
    table.add_column("Date", style="dim")
    table.add_column("Size", style="dim", justify="right")

    for i, log in enumerate(logs, 1):
        table.add_row(
            str(i),
            log.name,
            _extract_tool_name(log.name),
            _format_date(log),
            _format_size(log),
        )
    console.print(table)


def _view_log(console: Console, path: Path):
    """Display the full content of a log file."""
    content = path.read_text(errors="replace")
    console.rule(f"[bold cyan]{path.name}[/bold cyan]")
    try:
        syntax = Syntax(content, "text", theme="monokai", line_numbers=True)
        console.print(syntax)
    except Exception:
        console.print(content)
    console.rule()


def _delete_log(console: Console, path: Path) -> bool:
    """Delete a log file after confirmation. Returns True if deleted."""
    confirm = inquirer.confirm(message=f"Delete {path.name}?", default=False).execute()
    if confirm:
        path.unlink()
        console.print(f"[green]Deleted {path.name}[/green]")
        return True
    console.print("[yellow]Cancelled.[/yellow]")
    return False


def _search_logs(console: Console, logs: list[Path]):
    """Search all log files for a keyword and display matching lines."""
    keyword = inquirer.text(message="Search keyword:").execute()
    if not keyword:
        return

    console.rule(f"[bold cyan]Search: {keyword}[/bold cyan]")
    found = False
    for log in logs:
        try:
            lines = log.read_text(errors="replace").splitlines()
        except Exception:
            continue
        matches = [
            (i + 1, line)
            for i, line in enumerate(lines)
            if keyword.lower() in line.lower()
        ]
        if matches:
            found = True
            console.print(f"\n[bold yellow]{log.name}[/bold yellow]")
            for lineno, line in matches:
                console.print(f"  [dim]{lineno:>5}[/dim] | {line}")

    if not found:
        console.print(f"[red]No matches for '{keyword}'.[/red]")
    console.rule()


def run(console: Console):
    """Scan history browser entry point."""
    while True:
        logs = _get_logs()
        if not logs:
            console.print("[red]No scan logs found in ~/sectools-logs/[/red]")
            return

        _show_table(console, logs)

        action = inquirer.select(
            message="Action:",
            choices=["View", "Delete", "Search", "Back"],
            pointer="❯",
        ).execute()

        if action == "Back":
            return

        if action == "Search":
            _search_logs(console, logs)
            continue

        # View or Delete require picking a log
        names = [log.name for log in logs]
        chosen = inquirer.select(
            message="Select log:", choices=names, pointer="❯"
        ).execute()
        path = LOGS_DIR / chosen

        if action == "View":
            _view_log(console, path)
        elif action == "Delete":
            _delete_log(console, path)
