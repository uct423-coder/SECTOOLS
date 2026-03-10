import threading
import datetime
from rich.console import Console
from rich.table import Table
from InquirerPy import inquirer

from sectools.notifications import notify

SCHEDULED_TASKS: list[dict] = []  # In-memory only; tasks are lost on exit

# Tool name -> (module, function_name)
_TOOL_MAP = {
    "Nmap — Fast Scan": ("sectools.nmap_tool", "run"),
    "Nikto — Standard Scan": ("sectools.nikto_tool", "run"),
    "Gobuster — Dir Scan": ("sectools.gobuster_tool", "run"),
    "SQLMap — Basic Scan": ("sectools.sqlmap_tool", "run"),
    "Recon Autopilot": ("sectools.recon_tool", "run"),
}


def _run_task(task: dict, console: Console):
    """Execute a scheduled scan task."""
    if task.get("cancelled"):
        return

    tool_name = task["tool"]
    task["last_run"] = datetime.datetime.now().strftime("%H:%M:%S")
    task["runs"] += 1

    try:
        import importlib
        mod = importlib.import_module(task["module"])
        func = getattr(mod, task["func"])
        console.print(f"\n[bold yellow]⏰ Scheduled scan starting: {tool_name}[/bold yellow]")
        func(console)
        notify("SecTools Scheduler", f"Scheduled scan complete: {tool_name}")
    except Exception as e:
        console.print(f"[red]Scheduled scan error: {e}[/red]")

    # Reschedule if repeating
    if task.get("repeat") and not task.get("cancelled"):
        timer = threading.Timer(task["interval"], _run_task, args=(task, console))
        timer.daemon = True
        task["timer"] = timer
        timer.start()


def schedule_scan(console: Console):
    """Schedule a scan to run after a delay, optionally repeating."""
    tool = inquirer.select(
        message="Tool to schedule:",
        choices=list(_TOOL_MAP.keys()),
        pointer="❯",
    ).execute()

    minutes = inquirer.text(message="Run after how many minutes?", default="5").execute().strip()
    try:
        interval = float(minutes) * 60
    except ValueError:
        console.print("[red]Invalid number.[/red]")
        return

    repeat = inquirer.confirm(message="Repeat on this interval?", default=False).execute()

    mod_name, func_name = _TOOL_MAP[tool]
    task = {
        "tool": tool,
        "module": mod_name,
        "func": func_name,
        "interval": interval,
        "repeat": repeat,
        "runs": 0,
        "last_run": None,
        "cancelled": False,
        "created": datetime.datetime.now().strftime("%H:%M:%S"),
    }

    timer = threading.Timer(interval, _run_task, args=(task, console))
    timer.daemon = True
    task["timer"] = timer
    timer.start()

    SCHEDULED_TASKS.append(task)
    label = f"every {minutes} min" if repeat else f"in {minutes} min"
    console.print(f"[green]Scheduled: {tool} — {label}[/green]")


def view_scheduled(console: Console):
    """View and optionally cancel scheduled scans."""
    active = [t for t in SCHEDULED_TASKS if not t.get("cancelled")]
    if not active:
        console.print("[yellow]No scheduled scans.[/yellow]")
        return

    table = Table(title="Scheduled Scans", border_style="dim")
    table.add_column("#", style="cyan")
    table.add_column("Tool")
    table.add_column("Repeat")
    table.add_column("Interval")
    table.add_column("Runs", justify="right")
    table.add_column("Last Run")

    for i, t in enumerate(active, 1):
        mins = t["interval"] / 60
        table.add_row(
            str(i), t["tool"],
            "Yes" if t["repeat"] else "No",
            f"{mins:.0f} min",
            str(t["runs"]),
            t["last_run"] or "—",
        )
    console.print(table)

    if inquirer.confirm(message="Cancel a scan?", default=False).execute():
        idx = inquirer.text(message="Scan # to cancel:").execute().strip()
        try:
            task = active[int(idx) - 1]
            task["cancelled"] = True
            if task.get("timer"):
                task["timer"].cancel()
            console.print("[green]Cancelled.[/green]")
        except (ValueError, IndexError):
            console.print("[red]Invalid selection.[/red]")
