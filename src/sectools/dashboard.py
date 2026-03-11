"""Interactive startup dashboard using Rich panels and tables."""

import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text

from sectools.utils import LOGS_DIR, load_targets, TOOL_BINARIES, check_installed
from sectools.config import load_config
from sectools.tips import get_tip

VERSION = "2.1.0"

BANNER_LINES = [
    "   ____            _____           _",
    "  / ___|  ___  ___|_   _|__   ___ | |___",
    "  \\___ \\ / _ \\/ __| | |/ _ \\ / _ \\| / __|",
    "   ___) |  __/ (__  | | (_) | (_) | \\__ \\",
    "  |____/ \\___|\\___| |_|\\___/ \\___/|_|___/",
]

_GRADIENT_COLORS = ["cyan", "bright_cyan", "blue", "bright_blue", "magenta"]
_WHATS_NEW_FLAG = Path.home() / ".sectools" / ".v2_seen"


def _render_banner() -> Text:
    """Build the banner with a vertical gradient."""
    text = Text()
    for i, line in enumerate(BANNER_LINES):
        color = _GRADIENT_COLORS[i % len(_GRADIENT_COLORS)]
        text.append(line, style=f"bold {color}")
        text.append("\n")
    return text


def _gradient_line(width: int = 60) -> Text:
    """Return a horizontal gradient divider line."""
    chars = "━" * width
    seg = max(width // 5, 1)
    text = Text()
    colors = ["cyan", "bright_cyan", "blue", "bright_blue", "magenta"]
    for i, color in enumerate(colors):
        start = i * seg
        end = start + seg if i < len(colors) - 1 else width
        text.append(chars[start:end], style=f"bold {color}")
    return text


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


def _recent_scans(n: int = 5) -> list[dict]:
    """Return the last n scan log entries with metadata."""
    if not LOGS_DIR.exists():
        return []
    logs = sorted(LOGS_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    results = []
    for f in logs[:n]:
        stat = f.stat()
        results.append({
            "name": f.name,
            "time": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "size": _format_size(stat.st_size),
        })
    return results


def _should_show_whats_new() -> bool:
    """Check whether the v2.0 splash should display."""
    if _WHATS_NEW_FLAG.exists():
        return False
    return True


def _mark_whats_new_seen():
    """Write the flag file so the splash only shows once."""
    _WHATS_NEW_FLAG.parent.mkdir(parents=True, exist_ok=True)
    _WHATS_NEW_FLAG.touch()


def show_dashboard(console: Console):
    """Display the startup dashboard."""
    config = load_config()
    theme = config.get("theme_color", "cyan")

    # Session indicator
    from sectools.sessions import get_active_session
    session = get_active_session()

    # Header
    subtitle = f"v{VERSION}"
    if session:
        subtitle += f"  ·  Session: {session}"

    console.print()
    console.print(_render_banner())
    console.print(f"  ", end="")
    console.print(_gradient_line())
    console.print(f"  [dim]Made by Shepard Sotiroglou[/dim]  ·  [dim]{subtitle}[/dim]\n")

    # What's New (one-time after upgrade)
    if _should_show_whats_new():
        whats_new = Text.assemble(
            ("  NEW  ", "bold white on magenta"),
            ("  Visual overhaul with gradient banner and improved panels\n", ""),
            ("  NEW  ", "bold white on blue"),
            ("  Scan history now shows timestamps and file sizes\n", ""),
            ("  NEW  ", "bold white on cyan"),
            ("  Smarter tips panel with refreshed styling", ""),
        )
        console.print(Panel(
            whats_new,
            title="[bold bright_cyan]What's New in v2.0[/bold bright_cyan]",
            title_align="left",
            border_style="bright_cyan",
            padding=(1, 2),
        ))
        _mark_whats_new_seen()

    # Quick Stats
    targets_count = len(load_targets())
    scans_count = _count_logs()
    inst, total = _tools_installed_count()
    disk = _log_disk_usage()

    stats = [
        Panel(
            Text.assemble(("🎯 ", ""), (str(targets_count), "bold bright_green"), ("\n", ""), ("Targets", "dim")),
            border_style="green", expand=True,
        ),
        Panel(
            Text.assemble(("📡 ", ""), (str(scans_count), "bold bright_blue"), ("\n", ""), ("Scans", "dim")),
            border_style="blue", expand=True,
        ),
        Panel(
            Text.assemble(("🔧 ", ""), (f"{inst}", "bold bright_yellow"), (f"/{total}", "dim"), ("\n", ""), ("Tools", "dim")),
            border_style="yellow", expand=True,
        ),
        Panel(
            Text.assemble(("💾 ", ""), (disk, "bold bright_magenta"), ("\n", ""), ("Log Size", "dim")),
            border_style="magenta", expand=True,
        ),
    ]
    console.print(Columns(stats, equal=True, expand=True))

    # Recent Scans
    recent = _recent_scans()
    if recent:
        scan_table = Table(border_style="dim", expand=True, show_header=True, header_style="bold " + theme)
        scan_table.add_column("Scan Log", style=theme, ratio=3)
        scan_table.add_column("Date / Time", style="dim", ratio=2, justify="center")
        scan_table.add_column("Size", style="dim", ratio=1, justify="right")
        for entry in recent:
            scan_table.add_row(entry["name"], entry["time"], entry["size"])
        console.print(Panel(scan_table, title="[bold]📋 Recent Scans[/bold]", border_style="blue"))
    else:
        console.print(Panel("[dim]No scan logs yet. Run your first scan![/dim]", title="[bold]📋 Recent Scans[/bold]", border_style="blue"))

    # Tip of the Day
    tip_text = Text.assemble(
        ("» ", "bold bright_yellow"),
        (get_tip(), "italic"),
    )
    console.print(
        Panel(
            tip_text,
            title="[bold bright_yellow]💡 Tip of the Day[/bold bright_yellow]",
            title_align="left",
            border_style="bright_yellow",
            padding=(0, 2),
        )
    )

    # Quick Actions hint
    console.print(
        f"  [dim]⚡ Quick Launch:[/dim] [bold dim]n[/bold dim][dim]=Nmap  s=SQLMap  g=Gobuster  r=Recon  o=OSINT[/dim]\n"
    )
