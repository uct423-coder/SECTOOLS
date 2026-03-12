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
    "wpscan": "wpscan",
    "ffuf": "ffuf",
    "nuclei": "nuclei",
    "enum4linux": "enum4linux",
    "whatweb": "whatweb",
    "masscan": "masscan",
    "subfinder": "subfinder",
    "wafw00f": "wafw00f",
    "dirb": "dirb",
    "sslscan": "sslscan",
    "dig": "bind",
    "whois": "whois",
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
    "wpscan": "wpscan",
    "ffuf": "ffuf",
    "nuclei": "nuclei",
    "enum4linux": "enum4linux",
    "whatweb": "whatweb",
    "masscan": "masscan",
    "subfinder": "subfinder",
    "wafw00f": "wafw00f",
    "dirb": "dirb",
    "sslscan": "sslscan",
    "dig": "dnsutils",
    "whois": "whois",
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
    "wpscan": "wpscan",
    "ffuf": "ffuf",
    "nuclei": "nuclei",
    "enum4linux": "enum4linux",
    "whatweb": "whatweb",
    "masscan": "masscan",
    "subfinder": "subfinder",
    "wafw00f": "wafw00f",
    "dirb": "dirb",
    "sslscan": "sslscan",
    "dig": "bind-toolsonly",
    "whois": "whois",
}

# Binaries that need brew --cask on macOS
BREW_CASK = {"msfconsole"}

# Binaries best installed via pip when no system package exists
PIP_PACKAGES = {"wafw00f": "wafw00f", "wpscan": "wpscan"}

# Binaries best installed via go install
GO_PACKAGES = {
    "subfinder": "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
    "nuclei": "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest",
    "ffuf": "github.com/ffuf/ffuf/v2@latest",
}


def _detect_platform() -> str:
    """Return 'macos', 'linux', or 'windows'."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "linux":
        return "linux"
    return "windows"


def _build_install_commands(binary: str, plat: str) -> list[list[str]]:
    """Return a list of install commands to try in order (first success wins)."""
    commands = []

    if plat == "macos":
        pkg = BREW_PACKAGES.get(binary, binary)
        if binary in BREW_CASK:
            commands.append(["brew", "install", "--cask", pkg])
        else:
            commands.append(["brew", "install", pkg])
    elif plat == "linux":
        pkg = APT_PACKAGES.get(binary, binary)
        commands.append(["sudo", "apt", "install", "-y", pkg])
    else:
        pkg = CHOCO_PACKAGES.get(binary, binary)
        commands.append(["choco", "install", "-y", pkg])

    # Fallback: pip install
    if binary in PIP_PACKAGES:
        commands.append(["pip3", "install", PIP_PACKAGES[binary]])

    # Fallback: go install
    if binary in GO_PACKAGES:
        commands.append(["go", "install", GO_PACKAGES[binary]])

    return commands


def _status_table(console: Console) -> list[str]:
    """Print a status table and return list of missing binaries."""
    table = Table(title="Tool Status", border_style="dim", show_lines=False)
    table.add_column("", width=3, justify="center")
    table.add_column("Tool", style="bold")
    table.add_column("Binary", style="dim")

    missing = []
    for tool, binary in TOOL_BINARIES.items():
        if check_installed(binary):
            icon = "[green]✔[/green]"
        else:
            icon = "[red]✘[/red]"
            missing.append(binary)
        table.add_row(icon, tool, binary)

    console.print(table)
    console.print()
    return missing


def run(console: Console):
    """Entry point: show tool status and offer to install missing tools."""
    console.print("\n[bold cyan]━━━ Auto-Installer ━━━[/bold cyan]\n")

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

    for i, binary in enumerate(missing, 1):
        commands = _build_install_commands(binary, plat)
        console.print(f"  [dim][{i}/{len(missing)}][/dim] Installing [bold]{binary}[/bold]...")
        installed = False
        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    console.print(f"       [green]✔ Installed[/green] [dim]({cmd[0]})[/dim]")
                    installed = True
                    break
            except FileNotFoundError:
                continue
            except subprocess.TimeoutExpired:
                console.print(f"       [yellow]⚠ Timed out with {cmd[0]}[/yellow]")
                continue
        if not installed:
            console.print(f"       [red]✘ Could not install {binary}[/red]")

    console.print("\n[bold]Updated status:[/bold]\n")
    _status_table(console)
