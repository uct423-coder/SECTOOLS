"""Interactive startup dashboard using Rich panels and tables."""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text

from sectools.utils import LOGS_DIR, load_targets, TOOL_BINARIES, check_installed
from sectools.config import load_config
from sectools.tips import get_tip

VERSION = "1.1.0"


def _format_size(size_bytes: int) -> str:
    """Format byte count as human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _count_logs() -> int:
    """Count scan log files."""
    if not LOGS_DIR.exists():
        return 0
    return len(list(LOGS_DIR.glob("*.log")))


def _log_disk_usage() -> str:
    """Sum sizes of all .log files in LOGS_DIR."""
    if not LOGS_DIR.exists():
        return "0 B"
    total = sum(f.stat().st_size for f in LOGS_DIR.glob("*.log"))
    return _format_size(total)


def _tools_installed_count() -> tuple[int, int]:
    """Return (installed, total) tool counts."""
    installed = sum(1 for b in TOOL_BINARIES.values() if check_installed(b))
    return installed, len(TOOL_BINARIES)


def _recent_scans(n: int = 5) -> list[str]:
    """Return the last n scan log filenames sorted by modification time."""
    if not LOGS_DIR.exists():
        return []
    logs = sorted(LOGS_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [f.name for f in logs[:n]]


def show_dashboard(console: Console):
    """Display the startup dashboard."""
    config = load_config()
    theme = config.get("theme_color", "cyan")

    # Session indicator
    from sectools.sessions import get_active_session
    session = get_active_session()

    # Header
    header_text = Text(justify="center")
    header_text.append("SecTools CLI\n", style="bold white")
    header_text.append("Made by Shepard Sotiroglou", style="dim")
    subtitle = f"v{VERSION}"
    if session:
        subtitle += f"  |  Session: {session}"
    header = Panel(
        header_text,
        subtitle=subtitle,
        border_style=theme,
    )
    console.print(header)

    # Quick Stats
    targets_count = len(load_targets())
    scans_count = _count_logs()
    inst, total = _tools_installed_count()
    disk = _log_disk_usage()

    stats = [
        Panel(f"[bold]{targets_count}[/bold]\nTargets saved", border_style="green", expand=True),
        Panel(f"[bold]{scans_count}[/bold]\nScans logged", border_style="blue", expand=True),
        Panel(f"[bold]{inst}/{total}[/bold]\nTools installed", border_style="yellow", expand=True),
        Panel(f"[bold]{disk}[/bold]\nLog disk usage", border_style="magenta", expand=True),
    ]
    console.print(Columns(stats, equal=True, expand=True))

    # Recent Scans
    recent = _recent_scans()
    if recent:
        scan_table = Table(border_style="dim", expand=True)
        scan_table.add_column("Recent Scans", style=theme)
        for name in recent:
            scan_table.add_row(name)
        console.print(Panel(scan_table, title="Recent Scans", border_style="dim"))
    else:
        console.print(Panel("[dim]No scan logs yet.[/dim]", title="Recent Scans", border_style="dim"))

    # Tip of the Day
    console.print(
        Panel(
            f"[bold]{get_tip()}[/bold]",
            title="Tip of the Day",
            border_style=theme,
        )
    )

    # Quick Actions hint
    console.print(
        Panel(
            "[bold]Select a tool from the menu below to get started[/bold]",
            border_style="dim",
        )
    )
    console.print()
