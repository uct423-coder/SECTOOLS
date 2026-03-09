"""Auto-install missing security tools based on the current platform."""

import platform
import subprocess
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

from sectools.utils import TOOL_BINARIES, check_installed

# Binary -> package name overrides per platform
BREW_PACKAGES = {
    "nmap": "nmap",
    "msfconsole": "metasploit",  # special: --cask
    "sqlmap": "sqlmap",
    "nikto": "nikto",
    "hydra": "hydra",
    "gobuster": "gobuster",
    "john": "john",
    "hashcat": "hashcat",
    "nc": "netcat",
}

APT_PACKAGES = {
    "nmap": "nmap",
    "msfconsole": "metasploit-framework",
    "sqlmap": "sqlmap",
    "nikto": "nikto",
    "hydra": "hydra",
    "gobuster": "gobuster",
    "john": "john",
    "hashcat": "hashcat",
    "nc": "netcat-openbsd",
}

CHOCO_PACKAGES = {
    "nmap": "nmap",
    "msfconsole": "metasploit",
    "sqlmap": "sqlmap",
    "nikto": "nikto",
    "hydra": "hydra",
    "gobuster": "gobuster",
    "john": "john",
    "hashcat": "hashcat",
    "nc": "netcat",
}

# Binaries that need brew --cask on macOS
BREW_CASK = {"msfconsole"}


def _detect_platform() -> str:
    """Return 'macos', 'linux', or 'windows'."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "linux":
        return "linux"
    return "windows"


def _build_install_command(binary: str, plat: str) -> list[str]:
    """Return the shell command list to install the given binary."""
    if plat == "macos":
        pkg = BREW_PACKAGES.get(binary, binary)
        if binary in BREW_CASK:
            return ["brew", "install", "--cask", pkg]
        return ["brew", "install", pkg]
    elif plat == "linux":
        pkg = APT_PACKAGES.get(binary, binary)
        return ["sudo", "apt", "install", "-y", pkg]
    else:
        pkg = CHOCO_PACKAGES.get(binary, binary)
        return ["choco", "install", "-y", pkg]


def _status_table(console: Console) -> list[str]:
    """Print a status table and return list of missing binaries."""
    table = Table(title="Tool Status", border_style="dim")
    table.add_column("Tool", style="cyan")
    table.add_column("Binary", style="dim")
    table.add_column("Status")

    missing = []
    for tool, binary in TOOL_BINARIES.items():
        if check_installed(binary):
            status = "[bold green]installed[/bold green]"
        else:
            status = "[bold red]missing[/bold red]"
            missing.append(binary)
        table.add_row(tool, binary, status)

    console.print(table)
    console.print()
    return missing


def run(console: Console):
    """Entry point: show tool status and offer to install missing tools."""
    console.print("\n[bold cyan]Auto-Installer[/bold cyan]\n")

    missing = _status_table(console)

    if not missing:
        console.print("[green]All tools are already installed.[/green]\n")
        return

    console.print(f"[yellow]{len(missing)} tool(s) missing:[/yellow] {', '.join(missing)}\n")

    if not Confirm.ask("Install missing tools now?", default=False):
        console.print("[dim]Skipped.[/dim]\n")
        return

    plat = _detect_platform()
    console.print(f"[dim]Detected platform: {plat}[/dim]\n")

    for binary in missing:
        cmd = _build_install_command(binary, plat)
        console.print(f"[bold]Running:[/bold] {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                console.print(f"  [green]Success[/green]")
            else:
                console.print(f"  [red]Failed (exit {result.returncode})[/red]")
                if result.stderr.strip():
                    console.print(f"  [dim]{result.stderr.strip()[:200]}[/dim]")
        except FileNotFoundError:
            console.print(f"  [red]Package manager not found. Is it installed?[/red]")
        except subprocess.TimeoutExpired:
            console.print(f"  [red]Timed out after 5 minutes.[/red]")

    console.print("\n[bold]Updated status:[/bold]\n")
    _status_table(console)
