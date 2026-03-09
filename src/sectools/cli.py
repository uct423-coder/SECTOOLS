import sys
import os
import subprocess
from pathlib import Path


def get_repo_dir() -> Path:
    """Get the git repo root for the installed package."""
    # Walk up from this file to find .git
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
    print(f"Updating SecTools from {repo}...")

    result = subprocess.run(["git", "-C", str(repo), "pull", "--ff-only"],
                            capture_output=True, text=True)
    print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, end="")
        print("Update failed. Try: git pull manually.")
        sys.exit(1)

    # Reinstall package to pick up changes
    venv_pip = repo / ".venv" / "bin" / "pip"
    pip_cmd = str(venv_pip) if venv_pip.exists() else "pip3"
    subprocess.run([pip_cmd, "install", "-e", str(repo), "--quiet"])
    print("Update complete!")


def main():
    if len(sys.argv) < 2:
        print("Usage: sectool <command>")
        print("")
        print("Commands:")
        print("  start    Launch the SecTools menu")
        print("  update   Pull latest changes from git and reinstall")
        sys.exit(1)

    command = sys.argv[1]
    sys.argv = [sys.argv[0]] + sys.argv[2:]  # shift args

    commands = {
        "start": cmd_start,
        "update": cmd_update,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print("Available: start, update")
        sys.exit(1)


if __name__ == "__main__":
    main()
