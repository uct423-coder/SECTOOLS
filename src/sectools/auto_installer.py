"""Auto-install missing security tools based on the current platform."""

import platform
import shutil
import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

from sectools.utils import TOOL_BINARIES, check_installed

# ── macOS (Homebrew) ──────────────────────────────────────────────────
# Only list tools that actually exist in Homebrew
BREW_PACKAGES = {
    "nmap": "nmap",
    "sqlmap": "sqlmap",
    "nikto": "nikto",
    "hydra": "hydra",
    "gobuster": "gobuster",
    "john": "john",
    "hashcat": "hashcat",
    "nc": "netcat",
    "ffuf": "ffuf",
    "masscan": "masscan",
    "sslscan": "sslscan",
    "dig": "bind",
    "whois": "whois",
}

BREW_CASK = {"msfconsole": "metasploit"}

# ── Linux (apt) ───────────────────────────────────────────────────────
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
    "ffuf": "ffuf",
    "masscan": "masscan",
    "sslscan": "sslscan",
    "dig": "dnsutils",
    "whois": "whois",
    "enum4linux": "enum4linux",
    "dirb": "dirb",
    "whatweb": "whatweb",
    "wpscan": "wpscan",
    "wafw00f": "wafw00f",
    "subfinder": "subfinder",
    "nuclei": "nuclei",
}

# ── Windows (Chocolatey) ─────────────────────────────────────────────
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

# ── Cross-platform fallbacks ─────────────────────────────────────────
# pipx install (Python tools)
PIPX_PACKAGES = {
    "wafw00f": "wafw00f",
    "sqlmap": "sqlmap",
}

# gem install (Ruby tools)
GEM_PACKAGES = {
    "wpscan": "wpscan",
    "whatweb": "whatweb",
}

# go install (Go tools)
GO_PACKAGES = {
    "subfinder": "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
    "nuclei": "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest",
    "ffuf": "github.com/ffuf/ffuf/v2@latest",
    "gobuster": "github.com/OJ/gobuster/v3@latest",
}

# Git clone (tools with no package manager)
GIT_REPOS = {
    "enum4linux": "https://github.com/CiscoCXSecurity/enum4linux.git",
    "dirb": "https://github.com/v0re/dirb.git",
}

TOOLS_DIR = Path.home() / ".sectools-tools"


def _detect_platform() -> str:
    """Return 'macos', 'linux', or 'windows'."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "linux":
        return "linux"
    return "windows"


def _has(binary: str) -> bool:
    return shutil.which(binary) is not None


def _build_install_commands(binary: str, plat: str) -> list[tuple[list[str], str]]:
    """Return list of (command, description) tuples to try in order."""
    commands = []

    # Platform package manager first
    if plat == "macos":
        if binary in BREW_CASK:
            commands.append(
                (["brew", "install", "--cask", BREW_CASK[binary]], "brew (cask)")
            )
        elif binary in BREW_PACKAGES:
            commands.append(
                (["brew", "install", BREW_PACKAGES[binary]], "brew")
            )
    elif plat == "linux":
        if binary in APT_PACKAGES:
            commands.append(
                (["sudo", "apt", "install", "-y", APT_PACKAGES[binary]], "apt")
            )
    else:
        if binary in CHOCO_PACKAGES:
            commands.append(
                (["choco", "install", "-y", CHOCO_PACKAGES[binary]], "choco")
            )

    # pipx (preferred over raw pip — isolated environments)
    if binary in PIPX_PACKAGES and _has("pipx"):
        commands.append(
            (["pipx", "install", PIPX_PACKAGES[binary]], "pipx")
        )

    # gem
    if binary in GEM_PACKAGES and _has("gem"):
        commands.append(
            (["gem", "install", GEM_PACKAGES[binary]], "gem")
        )

    # go install
    if binary in GO_PACKAGES and _has("go"):
        commands.append(
            (["go", "install", GO_PACKAGES[binary]], "go")
        )

    # git clone as last resort
    if binary in GIT_REPOS:
        clone_dir = TOOLS_DIR / binary
        if not clone_dir.exists():
            commands.append(
                (["git", "clone", GIT_REPOS[binary], str(clone_dir)], "git clone")
            )

    return commands


def _post_install_git(binary: str, console: Console):
    """Set up git-cloned tools (symlink scripts to PATH)."""
    clone_dir = TOOLS_DIR / binary
    if not clone_dir.exists():
        return

    # Find the main script
    script = None
    for candidate in [clone_dir / f"{binary}.pl", clone_dir / f"{binary}.py", clone_dir / binary]:
        if candidate.exists():
            script = candidate
            break

    if script is None:
        # Look for any executable or .pl/.py file
        for f in clone_dir.iterdir():
            if f.suffix in (".pl", ".py") and binary in f.stem:
                script = f
                break

    if script:
        script.chmod(0o755)
        # Create a wrapper in ~/.local/bin
        local_bin = Path.home() / ".local" / "bin"
        local_bin.mkdir(parents=True, exist_ok=True)
        wrapper = local_bin / binary
        if not wrapper.exists():
            wrapper.write_text(f"#!/bin/bash\nexec \"{script}\" \"$@\"\n")
            wrapper.chmod(0o755)
            console.print(f"       [dim]Linked to {wrapper}[/dim]")


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

    TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    for i, binary in enumerate(missing, 1):
        commands = _build_install_commands(binary, plat)
        console.print(f"  [dim][{i}/{len(missing)}][/dim] Installing [bold]{binary}[/bold]...")

        if not commands:
            console.print(f"       [red]✘ No install method available for {binary}[/red]")
            continue

        installed = False
        for cmd, method in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    console.print(f"       [green]✔ Installed[/green] [dim]via {method}[/dim]")
                    # Post-install for git clones
                    if method == "git clone":
                        _post_install_git(binary, console)
                    installed = True
                    break
                # If brew fails with "No formulae found", skip to next method
            except FileNotFoundError:
                continue
            except subprocess.TimeoutExpired:
                console.print(f"       [yellow]⚠ Timed out ({method}), trying next...[/yellow]")
                continue

        if not installed:
            console.print(f"       [red]✘ Could not install {binary}[/red]")
            # Show hint
            if binary in GEM_PACKAGES:
                console.print(f"       [dim]Try manually: gem install {GEM_PACKAGES[binary]}[/dim]")
            elif binary in PIPX_PACKAGES:
                console.print(f"       [dim]Try manually: pipx install {PIPX_PACKAGES[binary]}[/dim]")
            elif binary in GO_PACKAGES:
                console.print(f"       [dim]Try manually: go install {GO_PACKAGES[binary]}[/dim]")

    console.print("\n[bold]Updated status:[/bold]\n")
    _status_table(console)
