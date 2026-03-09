import os
import shutil
import subprocess
import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table

LOGS_DIR = Path.home() / "sectools-logs"
TARGETS_FILE = Path.home() / ".sectools-targets"

# Tool name -> binary name mapping
TOOL_BINARIES = {
    "Nmap": "nmap",
    "Metasploit": "msfconsole",
    "SQLMap": "sqlmap",
    "Nikto": "nikto",
    "Hydra": "hydra",
    "Gobuster": "gobuster",
    "John the Ripper": "john",
    "Hashcat": "hashcat",
    "Netcat": "nc",
}


def check_installed(binary: str) -> bool:
    """Check if a binary is available on PATH."""
    return shutil.which(binary) is not None


def show_tool_status(console: Console):
    """Display a table of all tools and their install status."""
    table = Table(title="Tool Status", border_style="dim")
    table.add_column("Tool", style="cyan")
    table.add_column("Binary", style="dim")
    table.add_column("Status")

    for tool, binary in TOOL_BINARIES.items():
        if check_installed(binary):
            status = "[bold green]installed[/bold green]"
        else:
            status = "[bold red]missing[/bold red]"
        table.add_row(tool, binary, status)

    console.print(table)
    console.print()


def extract_hostname(target: str) -> tuple[str, bool]:
    """Strip URL scheme and path, returning (hostname, was_modified)."""
    from urllib.parse import urlparse
    stripped = target.strip()
    if "://" in stripped:
        parsed = urlparse(stripped)
        hostname = parsed.hostname or stripped
        return hostname, hostname != stripped
    return stripped, False


def run_logged(cmd: list[str], console: Console, tool_name: str) -> subprocess.CompletedProcess:
    """Run a command, display it, capture output to a log file, and stream to terminal."""
    LOGS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = tool_name.lower().replace(" ", "_")
    log_file = LOGS_DIR / f"{safe_name}_{timestamp}.log"

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
    console.print(f"[dim]Log: {log_file}[/dim]\n")

    with open(log_file, "w") as f:
        f.write(f"# {tool_name} scan — {datetime.datetime.now().isoformat()}\n")
        f.write(f"# Command: {' '.join(cmd)}\n\n")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(line, end="", flush=True)
            f.write(line)
        process.wait()

    console.print(f"\n[green]Results saved to {log_file}[/green]")
    return process


def save_target(target: str):
    """Save a target to the targets file."""
    existing = load_targets()
    if target not in existing:
        with open(TARGETS_FILE, "a") as f:
            f.write(target + "\n")


def load_targets() -> list[str]:
    """Load saved targets."""
    if not TARGETS_FILE.exists():
        return []
    return [t.strip() for t in TARGETS_FILE.read_text().splitlines() if t.strip()]


def ask_target(console: Console, message: str = "Target (IP/hostname):") -> str | None:
    """Ask for a target with option to pick from saved targets."""
    from InquirerPy import inquirer

    saved = load_targets()
    if saved:
        choices = ["Enter new target"] + saved
        choice = inquirer.select(
            message="Select target:",
            choices=choices,
            pointer="❯",
        ).execute()

        if choice != "Enter new target":
            return choice

    target = inquirer.text(message=message).execute().strip()
    if not target:
        console.print("[red]No target provided.[/red]")
        return None

    save_target(target)
    return target


def generate_report(console: Console):
    """Generate an HTML report from recent log files."""
    if not LOGS_DIR.exists():
        console.print("[red]No logs found.[/red]")
        return

    logs = sorted(LOGS_DIR.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not logs:
        console.print("[red]No logs found.[/red]")
        return

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = LOGS_DIR / f"report_{timestamp}.html"

    html = [
        "<!DOCTYPE html><html><head>",
        "<title>SecTools Report</title>",
        "<style>",
        "body { background: #1a1a2e; color: #e0e0e0; font-family: 'Courier New', monospace; padding: 40px; }",
        "h1 { color: #00d4ff; border-bottom: 2px solid #00d4ff; padding-bottom: 10px; }",
        "h2 { color: #ff6b6b; margin-top: 30px; }",
        ".scan { background: #16213e; border: 1px solid #0f3460; border-radius: 8px; padding: 20px; margin: 15px 0; }",
        ".meta { color: #888; font-size: 0.85em; margin-bottom: 10px; }",
        "pre { background: #0a0a1a; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; }",
        ".badge { display: inline-block; background: #00d4ff; color: #000; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }",
        "</style></head><body>",
        f"<h1>SecTools Scan Report</h1>",
        f"<p class='meta'>Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
        f"<p><span class='badge'>{len(logs)} scans</span></p>",
    ]

    for log in logs[:20]:  # Last 20 scans
        content = log.read_text()
        name = log.stem.replace("_", " ").title()
        mtime = datetime.datetime.fromtimestamp(log.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        html.append(f"<div class='scan'><h2>{name}</h2>")
        html.append(f"<p class='meta'>{mtime}</p>")
        # Escape HTML
        safe_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html.append(f"<pre>{safe_content}</pre></div>")

    html.append("</body></html>")
    report_file.write_text("\n".join(html))
    console.print(f"[bold green]Report saved: {report_file}[/bold green]")

    # Open in browser
    import webbrowser
    webbrowser.open(f"file://{report_file}")
