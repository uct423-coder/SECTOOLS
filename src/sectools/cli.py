import sys
import os
import subprocess
from pathlib import Path


def get_repo_dir() -> Path:
    """Get the git repo root for the installed package."""
    # Try without resolving symlinks first (avoids nested symlink paths)
    for start in [Path(__file__).parent, Path(__file__).resolve().parent]:
        d = start
        while d != d.parent:
            if (d / ".git").exists():
                return d
            d = d.parent
    return Path.cwd()


def cmd_start():
    from sectools.main import main
    main()


def cmd_update():
    repo = get_repo_dir()

    # Get current commit before pull
    before = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()

    from rich.console import Console
    c = Console()
    c.print("[dim]Checking for updates...[/dim]")

    # Fetch first to check if there are remote changes
    subprocess.run(["git", "-C", str(repo), "fetch"], capture_output=True)

    # Check if local is behind remote
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "-uno"],
        capture_output=True, text=True,
    ).stdout

    if "Your branch is behind" in status:
        result = subprocess.run(
            ["git", "-C", str(repo), "pull", "--ff-only"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            c.print(f"[red]✘ Update failed.[/red] Try: git pull manually.")
            c.print(f"[dim]{result.stderr.strip()}[/dim]")
            sys.exit(1)

        after = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True,
        ).stdout.strip()

        # Show what changed
        log = subprocess.run(
            ["git", "-C", str(repo), "log", "--oneline", f"{before}..{after}"],
            capture_output=True, text=True,
        ).stdout.strip()

        c.print(f"[green]✔[/green] Updated: [dim]{before}[/dim] → [bold]{after}[/bold]")
        if log:
            c.print(f"\n[bold]New commits:[/bold]")
            for line in log.splitlines():
                c.print(f"  [dim]•[/dim] {line}")

        # Reinstall package to pick up changes
        scripts = "Scripts" if os.name == "nt" else "bin"
        venv_pip = repo / ".venv" / scripts / "pip"
        pip_cmd = str(venv_pip) if venv_pip.exists() else "pip3"
        subprocess.run([pip_cmd, "install", "-e", str(repo), "--quiet"])

        # Auto-install any missing tools
        c.print()
        from sectools.auto_installer import run as auto_install
        auto_install(c)

        c.print(f"\n[bold green]✔ Update complete![/bold green] Restart sectool to use the new version.")
    else:
        from sectools.dashboard import VERSION
        c.print(f"[green]✔[/green] Already on the latest version [dim](v{VERSION}, commit {before})[/dim]")


def cmd_version():
    from rich.console import Console
    from sectools.dashboard import VERSION
    Console().print(f"[bold cyan]SecTools[/bold cyan] [dim]v{VERSION}[/dim]")


def cmd_hash():
    """Quick hash ID from command line: sectool hash <hash_value>"""
    if len(sys.argv) < 1 or not sys.argv[0]:
        print("Usage: sectool hash <hash_value>")
        sys.exit(1)
    from rich.console import Console
    from sectools.hash_id import identify_hash
    console = Console()
    identify_hash(console, sys.argv[0])


def cmd_encode():
    """Quick encode: sectool encode base64 <text>"""
    if len(sys.argv) < 2:
        print("Usage: sectool encode <method> <text>")
        print("Methods: base64, url, hex, rot13")
        sys.exit(1)
    import base64
    from urllib.parse import quote
    import codecs
    method, text = sys.argv[0], " ".join(sys.argv[1:])
    methods = {
        "base64": lambda t: base64.b64encode(t.encode()).decode(),
        "url": lambda t: quote(t),
        "hex": lambda t: t.encode().hex(),
        "rot13": lambda t: codecs.encode(t, "rot_13"),
    }
    if method not in methods:
        print(f"Unknown method: {method}. Use: {', '.join(methods)}")
        sys.exit(1)
    print(methods[method](text))


def cmd_status():
    """Quick tool status check."""
    from rich.console import Console
    from sectools.utils import show_tool_status
    show_tool_status(Console())


def cmd_uninstall():
    """Uninstall SecTools: remove symlink, venv, and config files."""
    import shutil

    repo = get_repo_dir()
    print("Uninstalling SecTools...\n")

    # Remove global symlink
    for bin_dir in [Path("/opt/homebrew/bin"), Path("/usr/local/bin")]:
        link = bin_dir / "sectool"
        if link.exists() or link.is_symlink():
            try:
                link.unlink()
                print(f"  Removed symlink: {link}")
            except PermissionError:
                print(f"  Could not remove {link} — try: sudo rm {link}")

    # Remove venv
    venv_dir = repo / ".venv"
    if venv_dir.exists():
        shutil.rmtree(venv_dir)
        print(f"  Removed virtual environment: {venv_dir}")

    # Windows: remove sectool.bat wrapper
    if os.name == "nt":
        bat = repo / "sectool.bat"
        if bat.exists():
            bat.unlink()
            print(f"  Removed {bat}")

    # All config/data files and directories SecTools creates
    config_files = [
        Path.home() / ".sectools-config.json",
        Path.home() / ".sectools-targets",
        Path.home() / ".sectools-profiles.json",
        Path.home() / ".sectools-creds.json",
        Path.home() / ".sectools-scope.json",
        Path.home() / ".sectools-workflows.json",
        Path.home() / ".sectools-sessions.json",
    ]
    data_dirs = [
        Path.home() / "sectools-logs",
        Path.home() / ".sectools-wordlists",
        Path.home() / ".sectools-plugins",
    ]

    # Find any remaining .sectools-* files we might have missed
    for f in Path.home().glob(".sectools-*"):
        if f.is_file() and f not in config_files:
            config_files.append(f)
        elif f.is_dir() and f not in data_dirs:
            data_dirs.append(f)

    existing_files = [f for f in config_files if f.exists()]
    existing_dirs = [d for d in data_dirs if d.exists()]

    if existing_files or existing_dirs:
        print("\nUser data found:")
        for f in existing_files:
            size = f.stat().st_size
            print(f"  {f}  ({_human_size(size)})")
        for d in existing_dirs:
            total = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            print(f"  {d}/  ({_human_size(total)})")

        answer = input("\nDelete ALL user data? This cannot be undone. (y/N): ").strip().lower()
        if answer == "y":
            for f in existing_files:
                f.unlink()
                print(f"  Deleted {f}")
            for d in existing_dirs:
                shutil.rmtree(d)
                print(f"  Deleted {d}/")
            print("\n  All user data removed.")
        else:
            print("  Kept user data.")

    print(f"\nSecTools fully uninstalled. To remove the source code: rm -rf {repo}")


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f} {unit}"
        size /= 1024
    return f"{size:.0f} TB"


def cmd_reinstall():
    """Reinstall SecTools: recreate venv, reinstall package, relink."""
    import shutil

    from rich.console import Console
    c = Console()
    repo = get_repo_dir()
    c.print("\n[bold cyan]Reinstalling SecTools...[/bold cyan]\n")

    # Remove old venv
    venv_dir = repo / ".venv"
    if venv_dir.exists():
        shutil.rmtree(venv_dir)
        c.print("  [dim]✔[/dim] Removed old virtual environment")

    # Create new venv — use system python, not sys.executable (which may be the deleted venv python)
    import shutil as _shutil
    python_bin = _shutil.which("python3") or _shutil.which("python") or sys.executable
    c.print("  [dim]⟳[/dim] Creating virtual environment...")
    subprocess.run([python_bin, "-m", "venv", str(venv_dir)], check=True)

    # Install package
    scripts = "Scripts" if os.name == "nt" else "bin"
    pip_path = venv_dir / scripts / "pip"
    c.print("  [dim]⟳[/dim] Installing SecTools...")
    subprocess.run([str(pip_path), "install", "-e", str(repo), "--quiet"], check=True)

    # Relink
    sectool_bin = venv_dir / scripts / "sectool"
    for bin_dir in [Path("/opt/homebrew/bin"), Path("/usr/local/bin")]:
        if bin_dir.exists():
            link = bin_dir / "sectool"
            try:
                link.unlink(missing_ok=True)
                link.symlink_to(sectool_bin)
                c.print(f"  [dim]✔[/dim] Linked: {link} → {sectool_bin}")
            except PermissionError:
                c.print(f"  [red]✘[/red] Could not link {link} — try: sudo ln -sf {sectool_bin} {link}")
            break

    c.print(f"\n[bold green]✔ Reinstall complete![/bold green] Run: [cyan]sectool start[/cyan]")


def cmd_restart():
    """Restart SecTools: re-exec the 'sectool start' process."""
    from rich.console import Console
    console = Console()
    console.print("\n[bold cyan]↻[/bold cyan]  [bold]Restarting SecTools...[/bold]\n")
    exe = sys.executable
    os.execv(exe, [exe, "-m", "sectools.cli", "start"])


def cmd_help():
    """Show help with all commands."""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from sectools.dashboard import VERSION

    console = Console()

    console.print()
    console.print(Panel.fit(
        f"[bold cyan]SecTools[/bold cyan] [dim]v{VERSION}[/dim]\n[dim]Made by Shepard Sotiroglou[/dim]",
        border_style="cyan",
    ))

    console.print(f"\n  [bold]Usage:[/bold] [cyan]sectool[/cyan] [dim]<command>[/dim]\n")

    table = Table(show_header=False, box=None, padding=(0, 2), expand=False)
    table.add_column("Command", style="bold cyan", min_width=12)
    table.add_column("Description")

    commands = [
        ("start",     "Launch the interactive menu"),
        ("restart",   "Restart SecTools"),
        ("update",    "Pull latest changes and reinstall"),
        ("reinstall", "Clean reinstall (recreate venv & relink)"),
        ("uninstall", "Remove SecTools completely"),
        ("version",   "Show version"),
        ("status",    "Show installed tool status"),
        ("hash",      "Identify a hash type — [dim]sectool hash <value>[/dim]"),
        ("encode",    "Quick encode — [dim]sectool encode <method> <text>[/dim]"),
        ("help",      "Show this help message"),
    ]
    for cmd, desc in commands:
        table.add_row(cmd, desc)

    console.print(table)

    console.print(f"\n  [bold]Flags:[/bold]")
    console.print(f"    [cyan]--dry-run[/cyan]   Show commands without executing")
    console.print(f"    [cyan]--json[/cyan]      Output results as JSON")
    console.print()


def main():
    commands = {
        "start": cmd_start,
        "restart": cmd_restart,
        "update": cmd_update,
        "version": cmd_version,
        "hash": cmd_hash,
        "encode": cmd_encode,
        "status": cmd_status,
        "uninstall": cmd_uninstall,
        "reinstall": cmd_reinstall,
        "help": cmd_help,
    }

    if len(sys.argv) < 2:
        cmd_help()
        sys.exit(1)

    # Parse global flags
    args = sys.argv[1:]
    if "--dry-run" in args:
        from sectools import utils
        utils.DRY_RUN = True
        args.remove("--dry-run")
    if "--json" in args:
        from sectools import utils
        utils.JSON_MODE = True
        args.remove("--json")

    if not args:
        cmd_help()
        sys.exit(1)

    command = args[0]
    sys.argv = args[1:]  # shift args for subcommand use

    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print(f"Available: {', '.join(commands)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
