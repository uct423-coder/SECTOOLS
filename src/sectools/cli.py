import sys
import os
import subprocess
from pathlib import Path


def get_repo_dir() -> Path:
    """Get the git repo root for the installed package."""
    d = Path(__file__).resolve().parent
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

    print(f"Checking for updates...")

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
            print(result.stderr, end="")
            print("Update failed. Try: git pull manually.")
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

        print(f"Updated: {before} → {after}")
        if log:
            print(f"\nNew commits:")
            for line in log.splitlines():
                print(f"  {line}")

        # Reinstall package to pick up changes
        venv_pip = repo / ".venv" / "bin" / "pip"
        pip_cmd = str(venv_pip) if venv_pip.exists() else "pip3"
        subprocess.run([pip_cmd, "install", "-e", str(repo), "--quiet"])
        print("\nUpdate complete! Restart sectool to use the new version.")
    else:
        from sectools.dashboard import VERSION
        print(f"Already on the latest version (v{VERSION}, commit {before}).")


def cmd_version():
    from sectools.dashboard import VERSION
    print(f"SecTools v{VERSION}")


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

    # Ask about config/data files
    config_files = [
        Path.home() / ".sectools-config.json",
        Path.home() / ".sectools-targets",
        Path.home() / ".sectools-profiles.json",
    ]
    data_dirs = [
        Path.home() / "sectools-logs",
        Path.home() / "sectools-wordlists",
        Path.home() / ".sectools-plugins",
    ]

    has_data = any(f.exists() for f in config_files) or any(d.exists() for d in data_dirs)
    if has_data:
        print("\nUser data found:")
        for f in config_files:
            if f.exists():
                print(f"  {f}")
        for d in data_dirs:
            if d.exists():
                print(f"  {d}/")

        answer = input("\nDelete user data too? (y/N): ").strip().lower()
        if answer == "y":
            for f in config_files:
                if f.exists():
                    f.unlink()
                    print(f"  Deleted {f}")
            for d in data_dirs:
                if d.exists():
                    shutil.rmtree(d)
                    print(f"  Deleted {d}/")
        else:
            print("  Kept user data.")

    print(f"\nSecTools uninstalled. To remove the source code: rm -rf {repo}")


def cmd_reinstall():
    """Reinstall SecTools: recreate venv, reinstall package, relink."""
    import shutil

    repo = get_repo_dir()
    print("Reinstalling SecTools...\n")

    # Remove old venv
    venv_dir = repo / ".venv"
    if venv_dir.exists():
        shutil.rmtree(venv_dir)
        print("  Removed old virtual environment")

    # Create new venv
    print("  Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    # Install package
    pip_path = venv_dir / "bin" / "pip"
    print("  Installing SecTools...")
    subprocess.run([str(pip_path), "install", "-e", str(repo), "--quiet"], check=True)

    # Relink
    sectool_bin = venv_dir / "bin" / "sectool"
    for bin_dir in [Path("/opt/homebrew/bin"), Path("/usr/local/bin")]:
        if bin_dir.exists():
            link = bin_dir / "sectool"
            try:
                link.unlink(missing_ok=True)
                link.symlink_to(sectool_bin)
                print(f"  Linked: {link} → {sectool_bin}")
            except PermissionError:
                print(f"  Could not link {link} — try: sudo ln -sf {sectool_bin} {link}")
            break

    print("\nReinstall complete! Run: sectool start")


def cmd_help():
    """Show help with all commands."""
    from sectools.dashboard import VERSION
    print(f"\033[1m\033[36mSecTools\033[0m v{VERSION}")
    print(f"\033[2mMade by Shepard Sotiroglou\033[0m")
    print("")
    print("Usage: sectool <command>")
    print("")
    print("Commands:")
    print("  start       Launch the SecTools interactive menu")
    print("  update      Pull latest changes from git and reinstall")
    print("  reinstall   Clean reinstall (recreate venv and relink)")
    print("  uninstall   Remove SecTools (venv, symlinks, optionally data)")
    print("  version     Show version")
    print("  status      Show installed tool status")
    print("  hash        Identify a hash type: sectool hash <value>")
    print("  encode      Quick encode: sectool encode <method> <text>")
    print("  help        Show this help message")


def main():
    commands = {
        "start": cmd_start,
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

    command = sys.argv[1]
    sys.argv = sys.argv[2:]  # shift args for subcommand use

    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print(f"Available: {', '.join(commands)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
